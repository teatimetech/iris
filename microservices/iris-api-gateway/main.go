package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
)

var db *sql.DB

// InitDB initializes the database connection
func InitDB() {
	var err error
	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		os.Getenv("DB_HOST"),
		os.Getenv("DB_PORT"),
		os.Getenv("DB_USER"),
		os.Getenv("DB_PASSWORD"),
		os.Getenv("DB_NAME"),
	)

	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	if err = db.Ping(); err != nil {
		log.Fatal("Failed to ping database:", err)
	}

	// Create chat_history table if not exists
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS chat_history (
			id SERIAL PRIMARY KEY,
			user_id VARCHAR(50) NOT NULL,
			role VARCHAR(20) NOT NULL,
			content TEXT NOT NULL,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		log.Fatal("Failed to create chat_history table:", err)
	}

	log.Println("✅ Successfully connected to Postgres and verified schema")
}

// Request/Response Schemas
type ChatRequest struct {
	UserID string `json:"user_id"`
	Prompt string `json:"prompt"`
}

type ChatResponse struct {
	Response string `json:"response"`
}

// Portfolio Data Structures
type Holding struct {
	Symbol        string  `json:"symbol"`
	Name          string  `json:"name"`
	Shares        float64 `json:"shares"`
	Price         float64 `json:"price"` // Current market price (mocked or fetched)
	Value         float64 `json:"value"`
	Change        float64 `json:"change"`
	ChangePercent float64 `json:"changePercent"`
}

type AllocationData struct {
	Name  string  `json:"name"`
	Value float64 `json:"value"`
	Color string  `json:"color"`
}

type PerformanceData struct {
	Date  string  `json:"date"`
	Value float64 `json:"value"`
}

type Portfolio struct {
	TotalValue     float64           `json:"totalValue"`
	TodayPL        float64           `json:"todayPL"`
	TodayPLPercent float64           `json:"todayPLPercent"`
	Holdings       []Holding         `json:"holdings"`
	Allocation     []AllocationData  `json:"allocation"`
	Performance    []PerformanceData `json:"performance"`
}

// Transaction Structure
type Transaction struct {
	Symbol    string    `json:"symbol"`
	Type      string    `json:"type"`
	Shares    float64   `json:"shares"`
	Price     float64   `json:"price"`
	Timestamp time.Time `json:"timestamp"`
}

// ChatMessage Structure
type ChatMessage struct {
	Role      string `json:"role"`
	Content   string `json:"content"`
	Timestamp string `json:"timestamp"`
}

// ChatHandler routes the user request to the Python Agent service
func ChatHandler(c *gin.Context) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request format"})
		return
	}

	// 1. Save User Prompt to History
	_, err := db.Exec("INSERT INTO chat_history (user_id, role, content) VALUES ($1, $2, $3)", req.UserID, "user", req.Prompt)
	if err != nil {
		log.Printf("Failed to save user message: %v", err)
		// Proceed anyway, logging is non-blocking for critical path
	}

	// Get Agent URL from environment variable (K8s Service DNS)
	agentURL := os.Getenv("AGENT_SERVICE_URL") + "/api/v1/chat"
	reqBody, _ := json.Marshal(req)

	// HTTP POST call to the Agent Router (uses internal Linkerd/mTLS path)
	resp, err := http.Post(agentURL, "application/json", bytes.NewBuffer(reqBody))
	if err != nil || resp.StatusCode != http.StatusOK {
		log.Printf("Agent Service connection failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Agent Service unavailable or failed processing"})
		return
	}
	defer resp.Body.Close()

	// Decode response from Agent Router
	var agentResp ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&agentResp); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decode agent response"})
		return
	}

	// 2. Save Agent Response to History
	_, err = db.Exec("INSERT INTO chat_history (user_id, role, content) VALUES ($1, $2, $3)", req.UserID, "ai", agentResp.Response)
	if err != nil {
		log.Printf("Failed to save ai message: %v", err)
	}

	c.JSON(http.StatusOK, agentResp)
}

// GetChatHistoryHandler returns recent chat messages
func GetChatHistoryHandler(c *gin.Context) {
	userID := c.Param("userId")

	rows, err := db.Query("SELECT role, content, timestamp FROM chat_history WHERE user_id = $1 ORDER BY timestamp DESC LIMIT 20", userID)
	if err != nil {
		// Log error but perform safe return
		log.Printf("Error querying chat history: %v", err)
		c.JSON(http.StatusOK, []ChatMessage{}) // Return empty list on error/no-rows to not break UI
		return
	}
	defer rows.Close()

	var history []ChatMessage
	for rows.Next() {
		var msg ChatMessage
		var ts time.Time
		if err := rows.Scan(&msg.Role, &msg.Content, &ts); err != nil {
			continue
		}
		msg.Timestamp = ts.Format(time.RFC3339)
		history = append(history, msg)
	}

	// Reverse to chronological order if needed, but agent might confusingly read backwards.
	// Let's standardise on returning chronological (oldest -> newest).
	// Since we queried with DESC (newest first), we should reverse it.

	// Actually, easier to query ASC with subquery or just reverse here.
	// Let's query ASC (LIMIT applies to recent?).
	// To get *most recent* 20 but in ASC order:
	// SELECT * FROM (SELECT ... ORDER BY timestamp DESC LIMIT 20) sub ORDER BY timestamp ASC;

	// Simplified (Go-side reverse):
	for i, j := 0, len(history)-1; i < j; i, j = i+1, j-1 {
		history[i], history[j] = history[j], history[i]
	}

	c.JSON(http.StatusOK, history)
}

// GetTransactionsHandler returns user transaction history
func GetTransactionsHandler(c *gin.Context) {
	userID := c.Param("userId")

	// Get Portfolio ID first
	var portfolioID int
	err := db.QueryRow("SELECT id FROM portfolios WHERE user_id = $1", userID).Scan(&portfolioID)
	if err != nil {
		c.JSON(http.StatusOK, []Transaction{}) // Return empty if no portfolio
		return
	}

	rows, err := db.Query("SELECT symbol, type, shares, price, timestamp FROM transactions WHERE portfolio_id = $1 ORDER BY timestamp DESC LIMIT 10", portfolioID)
	if err != nil {
		log.Printf("Error fetching transactions: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch transactions"})
		return
	}
	defer rows.Close()

	var transactions []Transaction
	for rows.Next() {
		var t Transaction
		if err := rows.Scan(&t.Symbol, &t.Type, &t.Shares, &t.Price, &t.Timestamp); err != nil {
			continue
		}
		transactions = append(transactions, t)
	}

	c.JSON(http.StatusOK, transactions)
}

// GetPortfolioHandler fetches portfolio data from Postgres
func GetPortfolioHandler(c *gin.Context) {
	userID := c.Param("userId")
	log.Printf("Fetching portfolio for user: %s", userID)

	// 1. Get Portfolio ID
	var portfolioID int
	err := db.QueryRow("SELECT id FROM portfolios WHERE user_id = $1", userID).Scan(&portfolioID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Portfolio not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// 2. Get Holdings
	rows, err := db.Query("SELECT symbol, shares, avg_price FROM holdings WHERE portfolio_id = $1", portfolioID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch holdings"})
		return
	}
	defer rows.Close()

	var holdings []Holding
	var totalValue float64

	for rows.Next() {
		var h Holding
		var avgPrice float64
		if err := rows.Scan(&h.Symbol, &h.Shares, &avgPrice); err != nil {
			continue
		}

		// In a real app, we would fetch live price here. For now, use avgPrice * 1.05 as mock current price
		h.Price = avgPrice * 1.05
		h.Value = h.Shares * h.Price
		h.Name = h.Symbol // Simplification
		h.Change = h.Price - avgPrice
		h.ChangePercent = (h.Change / avgPrice) * 100

		holdings = append(holdings, h)
		totalValue += h.Value
	}

	// 3. Construct Response
	portfolio := Portfolio{
		TotalValue:     totalValue,
		TodayPL:        totalValue * 0.05, // Mock data
		TodayPLPercent: 5.0,
		Holdings:       holdings,
		Allocation: []AllocationData{
			{Name: "Technology", Value: 65, Color: "#3b82f6"},
			{Name: "Other", Value: 35, Color: "#10b981"},
		},
		Performance: generatePerformanceData(),
	}

	c.JSON(http.StatusOK, portfolio)
}

// TradeRequest defines the body for executing a trade
type TradeRequest struct {
	UserID string  `json:"user_id"`
	Symbol string  `json:"symbol"`
	Action string  `json:"action"` // BUY or SELL
	Shares float64 `json:"shares"`
	Price  float64 `json:"price"` // Executed price
}

// ExecuteTradeHandler handles buying/selling assets
func ExecuteTradeHandler(c *gin.Context) {
	var req TradeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid trade request"})
		return
	}

	log.Printf("Executing trade: %s %v %s @ %v for %s", req.Action, req.Shares, req.Symbol, req.Price, req.UserID)

	// 1. Get Portfolio ID
	var portfolioID int
	err := db.QueryRow("SELECT id FROM portfolios WHERE user_id = $1", req.UserID).Scan(&portfolioID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Portfolio not found for user"})
		return
	}

	// 2. Insert Transaction Log
	_, err = db.Exec("INSERT INTO transactions (portfolio_id, symbol, type, shares, price) VALUES ($1, $2, $3, $4, $5)",
		portfolioID, req.Symbol, req.Action, req.Shares, req.Price)
	if err != nil {
		log.Printf("Failed to log transaction: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to record transaction"})
		return
	}

	// 3. Update Holdings
	// Simple logic: Check if exists, then update.
	// In a real app, we'd handle "SELL" validation (do we have enough shares?) and avg cost calculation.

	// Check current holding
	var currentShares float64
	err = db.QueryRow("SELECT shares FROM holdings WHERE portfolio_id = $1 AND symbol = $2", portfolioID, req.Symbol).Scan(&currentShares)

	if err == sql.ErrNoRows {
		// New holding (Only valid for BUY)
		if req.Action == "SELL" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot sell stock you do not own"})
			return
		}
		_, err = db.Exec("INSERT INTO holdings (portfolio_id, symbol, shares, avg_price) VALUES ($1, $2, $3, $4)",
			portfolioID, req.Symbol, req.Shares, req.Price)
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error checking holdings"})
		return
	} else {
		// Update existing holding
		newShares := currentShares
		if req.Action == "BUY" {
			newShares += req.Shares
			// Avg Price update omitted for simplicity in this demo, but should be: (old_val + new_val) / new_total_shares
		} else if req.Action == "SELL" {
			if currentShares < req.Shares {
				c.JSON(http.StatusBadRequest, gin.H{"error": "Insufficient shares to sell"})
				return
			}
			newShares -= req.Shares
		}

		if newShares == 0 {
			_, err = db.Exec("DELETE FROM holdings WHERE portfolio_id = $1 AND symbol = $2", portfolioID, req.Symbol)
		} else {
			_, err = db.Exec("UPDATE holdings SET shares = $1 WHERE portfolio_id = $2 AND symbol = $3",
				newShares, portfolioID, req.Symbol)
		}
	}

	if err != nil {
		log.Printf("Failed to update holdings: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update holdings"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":  "success",
		"message": fmt.Sprintf("Trade executed: %s %v %s", req.Action, req.Shares, req.Symbol),
	})
}

// generatePerformanceData creates 30 days of mock performance data
func generatePerformanceData() []PerformanceData {
	data := make([]PerformanceData, 30)
	baseValue := 120000.0
	for i := 0; i < 30; i++ {
		date := "2024-11-" + fmt.Sprintf("%02d", i+1)
		value := baseValue + float64(i)*200 + (float64(i%5) * 500)
		data[i] = PerformanceData{Date: date, Value: value}
	}
	return data
}

func main() {
	// Set Gin to release mode for low overhead
	gin.SetMode(gin.ReleaseMode)

	// Initialize Database
	InitDB()

	router := gin.New()
	router.Use(gin.Recovery())

	// CORS middleware for web-ui access
	allowOrigin := os.Getenv("ALLOW_ORIGIN")
	if allowOrigin == "" {
		allowOrigin = "http://localhost:3000"
	}
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", allowOrigin)
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Health check endpoint for Kubernetes probes
	router.GET("/health", func(c *gin.Context) {
		if err := db.Ping(); err != nil {
			c.JSON(503, gin.H{"status": "unhealthy", "db": "disconnected"})
			return
		}
		c.JSON(200, gin.H{
			"status":  "healthy",
			"service": "iris-api-gateway",
		})
	})

	v1 := router.Group("/v1")
	{
		v1.POST("/chat", ChatHandler)
		v1.GET("/chat/history/:userId", GetChatHistoryHandler)
		v1.GET("/portfolio/:userId", GetPortfolioHandler)
		v1.GET("/transactions/:userId", GetTransactionsHandler)
		v1.POST("/trade", ExecuteTradeHandler)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("IRIS API Gateway starting on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatal("Server failed to start: ", err)
	}
}
