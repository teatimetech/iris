package main

import (
	"database/sql"
	"fmt"
	"net/http"

	"bytes"
	"encoding/json"
	"iris-api-gateway/pkg/finance"
	"log"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/lib/pq"
)

// GetPortfolioHandler fetches portfolio data from Postgres with broker grouping
// Updated for Schema Refactoring: Joins through accounts table
func GetPortfolioHandler(c *gin.Context) {
	userID := c.Param("userId")
	log.Printf("Fetching portfolio for user: %s", userID)

	// 1. Get all portfolios for this user (grouped by broker)
	type portfolioRow struct {
		PortfolioID       int
		AccountID         string
		PortfolioName     string
		PortfolioType     string
		BrokerID          sql.NullInt64
		BrokerName        sql.NullString
		DisplayName       sql.NullString
		AccountNumber     sql.NullString
		AlpacaAccountId   sql.NullString
		IrisAccountNumber sql.NullString
		IrisAccountId     sql.NullString
		CashBalance       sql.NullFloat64
	}

	// Join accounts to get user portfolios
	portfolioRows, err := db.Query(`
		SELECT p.id, p.account_id, p.name, p.type, p.broker_id, b.name, b.display_name, a.alpaca_account_number, a.alpaca_account_id, p.iris_account_number, p.iris_account_id, p.cash_balance
		FROM portfolios p
		JOIN accounts a ON p.account_id = a.id
		LEFT JOIN brokers b ON p.broker_id = b.id
		WHERE a.user_id = $1
		ORDER BY b.display_name NULLS LAST, p.name
	`, userID)
	if err != nil {
		log.Printf("Error fetching portfolios: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch portfolios"})
		return
	}
	defer portfolioRows.Close()

	var portfolios []portfolioRow
	for portfolioRows.Next() {
		var p portfolioRow
		if err := portfolioRows.Scan(&p.PortfolioID, &p.AccountID, &p.PortfolioName, &p.PortfolioType, &p.BrokerID, &p.BrokerName, &p.DisplayName, &p.AccountNumber, &p.AlpacaAccountId, &p.IrisAccountNumber, &p.IrisAccountId, &p.CashBalance); err != nil {
			log.Printf("Error scanning portfolio row: %v", err)
			continue
		}

		// --- Real-time Alpaca Sync & Auto-Funding ---
		if p.PortfolioType == "IRIS Core" && p.AlpacaAccountId.Valid && p.AlpacaAccountId.String != "" {
			brokerURL := os.Getenv("BROKER_SERVICE_URL")
			if brokerURL == "" {
				brokerURL = "http://iris-broker-service:8081"
			}

			log.Printf("Syncing Alpaca account %s from Broker Service", p.AlpacaAccountId.String)
			resp, err := http.Get(fmt.Sprintf("%s/v1/portfolio/%s", brokerURL, p.AlpacaAccountId.String))
			if err == nil && resp.StatusCode == http.StatusOK {
				var bData struct {
					Account struct {
						Cash string `json:"cash"`
					} `json:"account"`
				}
				if err := json.NewDecoder(resp.Body).Decode(&bData); err == nil {
					cash, _ := strconv.ParseFloat(bData.Account.Cash, 64)
					log.Printf("Alpaca cash balance for %s: %v", p.AlpacaAccountId.String, cash)

					// Auto-funding logic: if balance is 0, add $25,000
					if cash <= 0 {
						log.Printf("Auto-funding account %s with $25,000", p.AlpacaAccountId.String)
						fundData := map[string]string{
							"account_id": p.AlpacaAccountId.String,
							"amount":     "25000",
						}
						fBytes, _ := json.Marshal(fundData)
						fResp, fErr := http.Post(fmt.Sprintf("%s/v1/funds", brokerURL), "application/json", bytes.NewBuffer(fBytes))
						if fErr == nil && fResp.StatusCode == http.StatusOK {
							log.Printf("Successfully funded account %s", p.AlpacaAccountId.String)
							cash = 25000 // Update local value to reflect funding
						} else if fErr != nil {
							log.Printf("Funding failed: %v", fErr)
						} else {
							log.Printf("Funding request returned status: %d", fResp.StatusCode)
						}
					}

					p.CashBalance.Float64 = cash
					p.CashBalance.Valid = true

					// Persist latest balance to DB
					_, dbErr := db.Exec("UPDATE portfolios SET cash_balance = $1, last_synced_at = NOW() WHERE id = $2", cash, p.PortfolioID)
					if dbErr != nil {
						log.Printf("Failed to update portfolio balance in DB: %v", dbErr)
					}
				}
				resp.Body.Close()
			} else if err != nil {
				log.Printf("Broker Service connection failed: %v", err)
			}
		}

		portfolios = append(portfolios, p)
	}

	if len(portfolios) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "No portfolios found"})
		return
	}

	// 2. Get holdings for all portfolios
	type holdingRow struct {
		PortfolioID   int
		Symbol        string
		Shares        float64
		AvgPrice      float64
		PurchaseDate  sql.NullTime
		YtdStartValue sql.NullFloat64
	}

	holdingsQuery := `
		SELECT portfolio_id, symbol, shares, avg_price, purchase_date, ytd_start_value
		FROM holdings
		WHERE portfolio_id = ANY($1)
	`

	portfolioIDs := make([]int, len(portfolios))
	for i, p := range portfolios {
		portfolioIDs[i] = p.PortfolioID
	}

	holdingRows, err := db.Query(holdingsQuery, pq.Array(portfolioIDs))
	if err != nil {
		log.Printf("Error fetching holdings: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch holdings"})
		return
	}
	defer holdingRows.Close()

	holdingsByPortfolio := make(map[int][]holdingRow)
	var allSymbols []string
	symbolSet := make(map[string]bool)

	for holdingRows.Next() {
		var h holdingRow
		if err := holdingRows.Scan(&h.PortfolioID, &h.Symbol, &h.Shares, &h.AvgPrice, &h.PurchaseDate, &h.YtdStartValue); err != nil {
			log.Printf("Error scanning holding: %v", err)
			continue
		}
		holdingsByPortfolio[h.PortfolioID] = append(holdingsByPortfolio[h.PortfolioID], h)
		if !symbolSet[h.Symbol] {
			allSymbols = append(allSymbols, h.Symbol)
			symbolSet[h.Symbol] = true
		}
	}

	// 3. Fetch real-time prices for all symbols
	finClient := finance.NewClient()
	quotes, err := finClient.GetQuotes(allSymbols)
	if err != nil {
		log.Printf("Error fetching quotes: %v", err)
		quotes = make(map[string]finance.Quote)
	}

	// 4. Build broker groups
	type brokerGroupKey struct {
		BrokerID      int
		BrokerName    string
		DisplayName   string
		PortfolioID   int
		PortfolioName string
		AccountNumber string
	}

	brokerMap := make(map[brokerGroupKey]*BrokerGroup)
	var totalValue, totalCost, totalGainLoss, todayPL, ytdPL, totalCashBalance float64

	for _, pRow := range portfolios {
		holdings := holdingsByPortfolio[pRow.PortfolioID]
		key := brokerGroupKey{
			BrokerID:      int(pRow.BrokerID.Int64),
			BrokerName:    pRow.BrokerName.String,
			DisplayName:   pRow.DisplayName.String,
			PortfolioID:   pRow.PortfolioID,
			PortfolioName: pRow.PortfolioName,
			AccountNumber: pRow.AccountNumber.String,
		}

		if key.DisplayName == "" {
			key.DisplayName = "Other Accounts"
		}

		group := &BrokerGroup{
			BrokerID:          key.BrokerID,
			BrokerName:        key.BrokerName,
			DisplayName:       key.DisplayName,
			AccountNumber:     key.AccountNumber,
			IrisAccountNumber: pRow.IrisAccountNumber.String,
			IrisAccountId:     pRow.IrisAccountId.String,
			PortfolioID:       key.PortfolioID,
			PortfolioName:     key.PortfolioName,
			CashBalance:       pRow.CashBalance.Float64,
			Holdings:          []Holding{},
		}

		// Fallback to Alpaca IDs if Iris IDs are not explicitly set in the database
		if group.IrisAccountNumber == "" {
			group.IrisAccountNumber = key.AccountNumber
		}
		if group.IrisAccountId == "" && pRow.AlpacaAccountId.Valid {
			group.IrisAccountId = pRow.AlpacaAccountId.String
		}

		groupTotalValue := 0.0
		groupTotalCost := 0.0

		for _, h := range holdings {
			q, ok := quotes[h.Symbol]
			currentPrice := h.AvgPrice
			dayChange := 0.0
			changePercent := 0.0

			if ok {
				currentPrice = q.RegularMarketPrice
				dayChange = q.RegularMarketChange
				changePercent = q.RegularMarketChangePercent
			}

			val := h.Shares * currentPrice
			cost := h.Shares * h.AvgPrice
			gainLoss := val - cost
			gainLossPercent := 0.0
			if cost > 0 {
				gainLossPercent = (gainLoss / cost) * 100
			}

			holding := Holding{
				Symbol:            h.Symbol,
				Name:              h.Symbol,
				Shares:            h.Shares,
				Price:             currentPrice,
				CostBasisPerShare: h.AvgPrice,
				Value:             val,
				CostBasis:         cost,
				Change:            dayChange,
				ChangePercent:     changePercent,
				GainLoss:          gainLoss,
				GainLossPercent:   gainLossPercent,
			}

			group.Holdings = append(group.Holdings, holding)
			groupTotalValue += val
			groupTotalCost += cost

			todayPL += (dayChange * h.Shares)
			totalGainLoss += gainLoss
			if h.YtdStartValue.Valid {
				ytdPL += (val - h.YtdStartValue.Float64)
			}
		}

		group.TotalValue = groupTotalValue + group.CashBalance
		group.TotalCost = groupTotalCost
		group.GainLoss = groupTotalValue - groupTotalCost
		if groupTotalCost > 0 {
			group.GainLossPercent = (group.GainLoss / groupTotalCost) * 100
		}

		totalValue += groupTotalValue
		totalCost += groupTotalCost
		totalCashBalance += group.CashBalance

		brokerMap[key] = group
	}

	var brokerGroups []BrokerGroup
	for _, group := range brokerMap {
		brokerGroups = append(brokerGroups, *group)
	}

	totalGainLossPercent := 0.0
	if totalCost > 0 {
		totalGainLossPercent = (totalGainLoss / totalCost) * 100
	}

	todayPLPercent := 0.0
	if (totalValue - todayPL) > 0 {
		todayPLPercent = (todayPL / (totalValue - todayPL)) * 100
	}

	ytdPLPercent := 0.0
	if (totalValue - ytdPL) > 0 {
		ytdPLPercent = (ytdPL / (totalValue - ytdPL)) * 100
	}

	formatPL := func(value, percent float64) string {
		sign := ""
		if value >= 0 {
			sign = "+"
		}
		return fmt.Sprintf("$%s%.2f (%.2f%%)", sign, value, percent)
	}

	response := Portfolio{
		TotalValue:           totalValue + totalCashBalance,
		CashBalance:          totalCashBalance,
		TotalCost:            totalCost,
		TotalGainLoss:        totalGainLoss,
		TotalGainLossPercent: totalGainLossPercent,
		TodayPL:              formatPL(todayPL, todayPLPercent),
		YtdPL:                formatPL(ytdPL, ytdPLPercent),
		OverallPL:            formatPL(totalGainLoss, totalGainLossPercent),
		TodayPLValue:         todayPL,
		TodayPLPercent:       todayPLPercent,
		YtdPLValue:           ytdPL,
		YtdPLPercent:         ytdPLPercent,
		BrokerGroups:         brokerGroups,
		Holdings:             []Holding{},
		Allocation: []AllocationData{
			{Name: "Equities", Value: 100, Color: "#3b82f6"},
		},
		Performance: generatePerformanceData(),
	}

	c.JSON(http.StatusOK, response)
}
