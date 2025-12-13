package finance

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

// Quote represents the market data for a single symbol
type Quote struct {
	Symbol                     string  `json:"symbol"`
	RegularMarketPrice         float64 `json:"regularMarketPrice"`
	RegularMarketChange        float64 `json:"regularMarketChange"`
	RegularMarketChangePercent float64 `json:"regularMarketChangePercent"`
	RegularMarketPreviousClose float64 `json:"regularMarketPreviousClose"`
}

// YahooQuoteResponse matches the JSON structure returned by Yahoo Finance
type YahooQuoteResponse struct {
	QuoteResponse struct {
		Result []Quote `json:"result"`
		Error  interface{} `json:"error"`
	} `json:"quoteResponse"`
}

// Client handles financial data fetching
type Client struct {
	httpClient *http.Client
}

// NewClient creates a new finance client
func NewClient() *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// GetQuotes fetches real-time data for a list of symbols
func (c *Client) GetQuotes(symbols []string) (map[string]Quote, error) {
	if len(symbols) == 0 {
		return map[string]Quote{}, nil
	}

	// Join symbols with comma (e.g. "NVDA,AAPL,^GSPC")
	joinedSymbols := strings.Join(symbols, ",")
	url := fmt.Sprintf("https://query1.finance.yahoo.com/v7/finance/quote?symbols=%s", joinedSymbols)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	// User-Agent is often required by Yahoo Finance to avoid 403s
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch quotes: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("yahoo finance api returned status: %d", resp.StatusCode)
	}

	var yResp YahooQuoteResponse
	if err := json.NewDecoder(resp.Body).Decode(&yResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	if yResp.QuoteResponse.Error != nil {
		return nil, fmt.Errorf("yahoo finance api error: %v", yResp.QuoteResponse.Error)
	}

	// Convert slice to map for O(1) lookup
	quotes := make(map[string]Quote)
	for _, q := range yResp.QuoteResponse.Result {
		quotes[q.Symbol] = q
	}

	return quotes, nil
}
