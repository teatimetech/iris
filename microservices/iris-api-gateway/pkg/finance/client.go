package finance

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"sync"
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
		Result []Quote     `json:"result"`
		Error  interface{} `json:"error"`
	} `json:"quoteResponse"`
}

// Client handles financial data fetching
type Client struct {
	httpClient *http.Client
	crumb      string
	crumbMutex sync.RWMutex
	crumbTime  time.Time
}

// NewClient creates a new finance client with cookie jar
func NewClient() *Client {
	jar, _ := cookiejar.New(nil)
	return &Client{
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
			Jar:     jar,
		},
	}
}

// getCrumb fetches a fresh crumb token from Yahoo Finance
func (c *Client) getCrumb() error {
	c.crumbMutex.Lock()
	defer c.crumbMutex.Unlock()

	// Check if we have a recent crumb (less than 30 minutes old)
	if c.crumb != "" && time.Since(c.crumbTime) < 30*time.Minute {
		return nil
	}

	// First, make a request to establish cookies
	baseURL := "https://fc.yahoo.com"
	req, err := http.NewRequest("GET", baseURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create base request: %v", err)
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to establish session: %v", err)
	}
	io.Copy(io.Discard, resp.Body)
	resp.Body.Close()

	// Now fetch the crumb
	crumbURL := "https://query2.finance.yahoo.com/v1/test/getcrumb"
	req, err = http.NewRequest("GET", crumbURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create crumb request: %v", err)
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")

	resp, err = c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch crumb: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("crumb request returned status: %d", resp.StatusCode)
	}

	crumbBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read crumb response: %v", err)
	}

	c.crumb = strings.TrimSpace(string(crumbBytes))
	c.crumbTime = time.Now()

	fmt.Printf("Successfully fetched crumb: %s\n", c.crumb)
	return nil
}

// GetQuotes fetches real-time data for a list of symbols
func (c *Client) GetQuotes(symbols []string) (map[string]Quote, error) {
	if len(symbols) == 0 {
		return map[string]Quote{}, nil
	}

	// Ensure we have a valid crumb
	if err := c.getCrumb(); err != nil {
		return nil, fmt.Errorf("failed to get crumb: %v", err)
	}

	// Join symbols with comma (e.g. "NVDA,AAPL,^GSPC")
	joinedSymbols := strings.Join(symbols, ",")

	// Read crumb safely
	c.crumbMutex.RLock()
	crumb := c.crumb
	c.crumbMutex.RUnlock()

	// Build URL with crumb parameter
	baseURL := "https://query2.finance.yahoo.com/v7/finance/quote"
	params := url.Values{}
	params.Add("symbols", joinedSymbols)
	if crumb != "" {
		params.Add("crumb", crumb)
	}
	fullURL := fmt.Sprintf("%s?%s", baseURL, params.Encode())

	req, err := http.NewRequest("GET", fullURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	// Set headers to mimic browser
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Referer", "https://finance.yahoo.com/")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch quotes: %v", err)
	}
	defer resp.Body.Close()

	// If we get 401, try refreshing the crumb once
	if resp.StatusCode == http.StatusUnauthorized {
		fmt.Println("Got 401, refreshing crumb and retrying...")

		// Force refresh crumb
		c.crumbMutex.Lock()
		c.crumb = ""
		c.crumbMutex.Unlock()

		if err := c.getCrumb(); err != nil {
			return nil, fmt.Errorf("failed to refresh crumb: %v", err)
		}

		// Retry the request
		c.crumbMutex.RLock()
		crumb = c.crumb
		c.crumbMutex.RUnlock()

		params.Set("crumb", crumb)
		fullURL = fmt.Sprintf("%s?%s", baseURL, params.Encode())

		req, err = http.NewRequest("GET", fullURL, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create retry request: %v", err)
		}

		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
		req.Header.Set("Accept", "application/json")
		req.Header.Set("Accept-Language", "en-US,en;q=0.5")
		req.Header.Set("Referer", "https://finance.yahoo.com/")

		resp, err = c.httpClient.Do(req)
		if err != nil {
			return nil, fmt.Errorf("failed to fetch quotes on retry: %v", err)
		}
		defer resp.Body.Close()
	}

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("yahoo finance api returned status: %d, body: %s", resp.StatusCode, string(bodyBytes))
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

	fmt.Printf("Successfully fetched %d quotes\n", len(quotes))
	return quotes, nil
}
