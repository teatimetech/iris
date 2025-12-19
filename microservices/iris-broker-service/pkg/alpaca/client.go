package alpaca

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/shopspring/decimal"
)

const (
	SandboxBaseURL = "https://broker-api.sandbox.alpaca.markets/v1"
	ProdBaseURL    = "https://broker-api.alpaca.markets/v1"
)

type Client struct {
	httpClient *http.Client
	baseURL    string
	dataURL    string
	apiKey     string
	apiSecret  string
}

// NewClient initializes the broker client
func NewClient(key, secret string, isSandbox bool) *Client {
	baseURL := ProdBaseURL
	if isSandbox {
		baseURL = SandboxBaseURL
	}
	return &Client{
		httpClient: &http.Client{Timeout: 10 * time.Second},
		baseURL:    baseURL,
		// Ref: https://docs.alpaca.markets/docs/api-v2-stock-market-data-reference
		dataURL:   "https://data.alpaca.markets/v2",
		apiKey:    key,
		apiSecret: secret,
	}
}

// ... (Existing Methods) ...

// doRequest handles the Basic Auth required for Broker API
func (c *Client) doRequest(method, endpoint string, body interface{}) (*http.Response, error) {
	var reqBody []byte
	var err error

	if body != nil {
		reqBody, err = json.Marshal(body)
		if err != nil {
			return nil, err
		}
	}

	req, err := http.NewRequest(method, c.baseURL+endpoint, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	// Broker API uses Basic Auth (Key:Secret)
	auth := base64.StdEncoding.EncodeToString([]byte(c.apiKey + ":" + c.apiSecret))
	req.Header.Add("Authorization", "Basic "+auth)
	req.Header.Add("Content-Type", "application/json")

	return c.httpClient.Do(req)
}

type AccountResp struct {
	ID             string `json:"id"`
	AccountNumber  string `json:"account_number"`
	Status         string `json:"status"`
	Currency       string `json:"currency"`
	LastEquity     string `json:"last_equity"`
	Equity         string `json:"equity"` // Add standard equity
	Cash           string `json:"cash"`
	BuyingPower    string `json:"buying_power"` // Add buying power
	PortfolioValue string `json:"portfolio_value"`
}

// GetAccount returns account details (Trading View) for a specific AccountID
func (c *Client) GetAccount(accountID string) (*AccountResp, error) {
	// Use Trading API proxy to get balances (cash, buying_power)
	resp, err := c.doRequest("GET", "/trading/accounts/"+accountID+"/account", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API Error: %s", string(body))
	}

	var acct AccountResp
	if err := json.NewDecoder(resp.Body).Decode(&acct); err != nil {
		return nil, err
	}
	return &acct, nil
}

// GetAllAccounts returns all accounts
func (c *Client) GetAllAccounts() ([]AccountResp, error) {
	resp, err := c.doRequest("GET", "/accounts", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API Error: %s", string(body))
	}

	var accts []AccountResp
	if err := json.NewDecoder(resp.Body).Decode(&accts); err != nil {
		return nil, err
	}
	return accts, nil
}

type Contact struct {
	EmailAddress  string   `json:"email_address"`
	PhoneNumber   string   `json:"phone_number"`
	StreetAddress []string `json:"street_address"`
	City          string   `json:"city"`
	State         string   `json:"state"`
	PostalCode    string   `json:"postal_code"`
	Country       string   `json:"country"`
}

type Identity struct {
	GivenName             string   `json:"given_name"`
	FamilyName            string   `json:"family_name"`
	DateOfBirth           string   `json:"date_of_birth"`
	TaxID                 string   `json:"tax_id"`
	TaxIDType             string   `json:"tax_id_type"`
	CountryOfTaxResidence string   `json:"country_of_tax_residence"`
	FundingSource         []string `json:"funding_source"`
}

type Disclosures struct {
	IsControlPerson             bool `json:"is_control_person"`
	IsAffiliatedExchangeOrFinra bool `json:"is_affiliated_exchange_or_finra"`
	IsPoliticallyExposed        bool `json:"is_politically_exposed"`
	ImmediateFamilyExposed      bool `json:"immediate_family_exposed"`
}

type Agreement struct {
	Agreement string `json:"agreement"`
	SignedAt  string `json:"signed_at"`
	IpAddress string `json:"ip_address"`
}

type CreateAccountReq struct {
	Contact     Contact     `json:"contact"`
	Identity    Identity    `json:"identity"`
	Disclosures Disclosures `json:"disclosures"`
	Agreements  []Agreement `json:"agreements"`
}

func (c *Client) CreateAccount(req CreateAccountReq) (*AccountResp, error) {
	resp, err := c.doRequest("POST", "/accounts", req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API Error: %s", string(body))
	}

	var acct AccountResp
	if err := json.NewDecoder(resp.Body).Decode(&acct); err != nil {
		return nil, err
	}
	return &acct, nil
}

type TradeReq struct {
	Symbol      string          `json:"symbol"`
	Qty         decimal.Decimal `json:"qty"`
	Side        string          `json:"side"`          // "buy" or "sell"
	Type        string          `json:"type"`          // "market" or "limit"
	TimeInForce string          `json:"time_in_force"` // "day", "gtc"
}

// SubmitOrderForAccount places a trade for a specific user ID
func (c *Client) SubmitOrderForAccount(accountID string, trade TradeReq) error {
	// URL pattern: /trading/accounts/{account_id}/orders
	endpoint := fmt.Sprintf("/trading/accounts/%s/orders", accountID)

	resp, err := c.doRequest("POST", endpoint, trade)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to place order, status: %d, body: %s", resp.StatusCode, string(body))
	}
	return nil
}

type Position struct {
	AssetID        string          `json:"asset_id"`
	Symbol         string          `json:"symbol"`
	Qty            decimal.Decimal `json:"qty"`
	MarketValue    decimal.Decimal `json:"market_value"`
	CostBasis      decimal.Decimal `json:"cost_basis"`
	UnrealizedPL   decimal.Decimal `json:"unrealized_pl"`
	UnrealizedPLPC decimal.Decimal `json:"unrealized_plpc"`
	CurrentPrice   decimal.Decimal `json:"current_price"`
	ChangeToday    decimal.Decimal `json:"change_today"`
	AssetClass     string          `json:"asset_class"`
}

// GetPositions returns all open positions for an account
func (c *Client) GetPositions(accountID string) ([]Position, error) {
	endpoint := fmt.Sprintf("/trading/accounts/%s/positions", accountID)
	resp, err := c.doRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to get positions, status: %d, body: %s", resp.StatusCode, string(body))
	}

	var positions []Position
	if err := json.NewDecoder(resp.Body).Decode(&positions); err != nil {
		return nil, err
	}
	return positions, nil
}

// ACHRelationshipReq defines body for linking a bank
type ACHRelationshipReq struct {
	AccountOwnerName  string `json:"account_owner_name"`
	BankAccountType   string `json:"bank_account_type"`
	BankAccountNumber string `json:"bank_account_number"`
	BankRoutingNumber string `json:"bank_routing_number"`
	Nickname          string `json:"nickname"`
}

type ACHRelationshipResp struct {
	ID string `json:"id"`
	// other fields ignored
}

func (c *Client) CreateACHRelationship(accountID string) (string, error) {
	endpoint := fmt.Sprintf("/accounts/%s/ach_relationships", accountID)
	req := ACHRelationshipReq{
		AccountOwnerName:  "Test User",
		BankAccountType:   "CHECKING",
		BankAccountNumber: "123456789012",
		BankRoutingNumber: "111000025", // Valid Chase Routing
		Nickname:          "Sandbox Bank",
	}

	resp, err := c.doRequest("POST", endpoint, req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("failed to create ach relationship: %s", string(body))
	}

	var rel ACHRelationshipResp
	if err := json.NewDecoder(resp.Body).Decode(&rel); err != nil {
		return "", err
	}
	return rel.ID, nil
}

// TransferReq defines the body for creating a transfer (funding)
type TransferReq struct {
	TransferType   string          `json:"transfer_type"`
	RelationshipID string          `json:"relationship_id"`
	Direction      string          `json:"direction"`
	Timing         string          `json:"timing"`
	Amount         decimal.Decimal `json:"amount"`
}

// AddFunds simulates a transfer to the account using the Transfers API (Sandbox/Broker)
func (c *Client) AddFunds(accountID string, amount decimal.Decimal) error {
	// ... (existing code) ...
	return nil // Mocking the end of previous function to append new ones
}

// Asset represents a tradable instrument
type Asset struct {
	ID           string `json:"id"`
	Class        string `json:"class"`
	Exchange     string `json:"exchange"`
	Symbol       string `json:"symbol"`
	Status       string `json:"status"`
	Tradable     bool   `json:"tradable"`
	Marginable   bool   `json:"marginable"`
	Shortable    bool   `json:"shortable"`
	EasyToBorrow bool   `json:"easy_to_borrow"`
}

// GetAsset returns asset details
func (c *Client) GetAsset(symbol string) (*Asset, error) {
	resp, err := c.doRequest("GET", "/assets/"+symbol, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("asset not found or unavailable")
	}

	var asset Asset
	if err := json.NewDecoder(resp.Body).Decode(&asset); err != nil {
		return nil, err
	}
	return &asset, nil
}

// Quote represents a market quote
type Quote struct {
	Symbol    string    `json:"symbol"`
	AskPrice  float64   `json:"ap"`
	AskSize   float64   `json:"as"`
	BidPrice  float64   `json:"bp"`
	BidSize   float64   `json:"bs"`
	Timestamp time.Time `json:"t"`
}

// GetQuote returns the latest IEX quote using Data API v2
func (c *Client) GetQuote(symbol string) (*Quote, error) {
	// Endpoint: /v2/stocks/{symbol}/quotes/latest?feed=iex
	endpoint := fmt.Sprintf("%s/stocks/%s/quotes/latest?feed=iex", c.dataURL, symbol)

	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Add("APCA-API-KEY-ID", c.apiKey)
	req.Header.Add("APCA-API-SECRET-KEY", c.apiSecret)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Data API Error (%d): %s", resp.StatusCode, string(body))
	}

	// Response format V2: { "quote": { "ap": ..., "bp": ..., "t": ... }, "symbol": "AAPL" }
	// Struct wrapper needed
	var result struct {
		Quote  Quote  `json:"quote"`
		Symbol string `json:"symbol"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	// Map to our Quote struct
	q := result.Quote
	q.Symbol = symbol // Start with requested symbol
	if result.Symbol != "" {
		q.Symbol = result.Symbol
	}

	return &q, nil
}
