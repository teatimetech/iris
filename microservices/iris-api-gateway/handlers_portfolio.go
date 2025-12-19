package main

import (
	"database/sql"
	"fmt"
	"net/http"

	"iris-api-gateway/pkg/finance"
	"log"

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
		PortfolioID   int
		PortfolioName string
		PortfolioType string
		BrokerID      sql.NullInt64
		BrokerName    sql.NullString
		DisplayName   sql.NullString
		AccountNumber sql.NullString  // Alpaca Account Number from Accounts table
		CashBalance   sql.NullFloat64 // Added cash balance
	}

	// Join accounts to get user portfolios
	// Portfolios are now linked to Accounts, which are linked to Users.
	portfolioRows, err := db.Query(`
		SELECT p.id, p.name, p.type, p.broker_id, b.name, b.display_name, a.alpaca_account_number, p.cash_balance
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
		if err := portfolioRows.Scan(&p.PortfolioID, &p.PortfolioName, &p.PortfolioType, &p.BrokerID, &p.BrokerName, &p.DisplayName, &p.AccountNumber, &p.CashBalance); err != nil {
			log.Printf("Error scanning portfolio row: %v", err)
			continue
		}
		portfolios = append(portfolios, p)
	}

	if len(portfolios) == 0 {
		// New schema: User might exist but have no portfolios if signup failed partly, or just new user.
		// But SignUpHandler creates a default portfolio.
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
		SELECT portfolio_id, symbol, shares, avg_price, 
		       purchase_date, ytd_start_value
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
		// Continue with empty quotes - will use cost basis as fallback
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

	// Map to store BrokerGroup pointers
	brokerMap := make(map[brokerGroupKey]*BrokerGroup)
	// We also need to return a list, but the structure in the response depends on how the frontend expects it.
	// existing code seemed to return a flat list of portfolios or groups.
	// Let's stick to the previous 'BrokerGroups' structure which seemed to be []BrokerGroup in the Portfolio response?
	// Wait, the Portfolio struct (in main.go) has BrokerGroups []BrokerGroup.
	// This handler returns JSON. Let's check what it constructed.
	// It constructed a Portfolio object at the end.

	var totalValue, totalCost, totalGainLoss, todayPL, ytdPL, totalCashBalance float64

	// Helper to find or create group
	// Note: previous implementation grouped by Broker+Portfolio.

	for _, pRow := range portfolios {
		holdings := holdingsByPortfolio[pRow.PortfolioID]
		// Even if no holdings, we might want to show the portfolio

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

		// In the new schema, type 'IRIS Core' vs 'IRIS Crypto'
		// We could append the type to the name if useful, or handle it in UI.
		// For now, let's keep it simple.

		group := &BrokerGroup{
			BrokerID:      key.BrokerID,
			BrokerName:    key.BrokerName,
			DisplayName:   key.DisplayName,
			AccountNumber: key.AccountNumber,
			PortfolioID:   key.PortfolioID,   // Added field to BrokerGroup struct if missing in main.go, check main.go definition
			PortfolioName: key.PortfolioName, // Added field
			CashBalance:   pRow.CashBalance.Float64,
			Holdings:      []Holding{},
		}

		// Note: The main.go definition of BrokerGroup I saw earlier:
		/*
			type BrokerGroup struct {
				BrokerID        int       `json:"brokerId"`
				BrokerName      string    `json:"brokerName"`
				DisplayName     string    `json:"displayName"`
				AccountNumber   string    `json:"accountNumber"`
				PortfolioID     int       `json:"portfolioId"`
				PortfolioName   string    `json:"portfolioName"`
				...
			}
		*/
		// So those fields exist.

		for _, h := range holdings {
			q, ok := quotes[h.Symbol]
			currentPrice := h.AvgPrice // Fallback to cost basis
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
				Name:              h.Symbol, // We don't have name in DB yet, use symbol
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

			// Accumulate metrics
			totalValue += val
			totalCost += cost
			todayPL += (dayChange * h.Shares)

			if h.YtdStartValue.Valid {
				ytdPL += (val - h.YtdStartValue.Float64)
			}
		}

		// Total Value for group includes Cash
		group.TotalValue = totalValue + group.CashBalance
		group.TotalCost = totalCost // Cash doesn't have cost basis in this context, or it's 1:1. Let's keep cost to holdings.

		// Accumulate global cash
		totalCashBalance += group.CashBalance
		group.TotalCost = totalCost
		group.GainLoss = totalValue - totalCost
		if totalCost > 0 {
			group.GainLossPercent = (group.GainLoss / totalCost) * 100
		}

		brokerMap[key] = group
	}

	// Convert map to slice
	var brokerGroups []BrokerGroup
	for _, group := range brokerMap {
		brokerGroups = append(brokerGroups, *group)
	}

	var totalGainLossPercent float64
	if totalCost > 0 {
		totalGainLossPercent = (totalGainLoss / totalCost) * 100
	}

	todayPLPercent := 0.0
	prevDayVal := totalValue - todayPL
	if prevDayVal > 0 {
		todayPLPercent = (todayPL / prevDayVal) * 100
	}

	ytdPLPercent := 0.0
	ytdStartVal := totalValue - ytdPL
	if ytdStartVal > 0 {
		ytdPLPercent = (ytdPL / ytdStartVal) * 100
	}

	// Construct final response
	// Helper for formatting
	formatPL := func(value, percent float64) string {
		sign := ""
		if value >= 0 {
			sign = "+"
		}
		return fmt.Sprintf("$%s%.2f (%.2f%%)", sign, value, percent)
	}

	// Construct final response using Portfolio struct
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
		Holdings:             []Holding{}, // Empty for legacy flat holdings if not used, or flatten brokerGroups.Holdings if needed
		Allocation: []AllocationData{
			{Name: "Equities", Value: 100, Color: "#3b82f6"},
		},
		Performance: generatePerformanceData(),
	}

	c.JSON(http.StatusOK, response)
}
