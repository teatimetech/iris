package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
)

// Auth Request/Response Structures
type SignUpRequest struct {
	FirstName  string `json:"first_name" binding:"required"`
	LastName   string `json:"last_name" binding:"required"`
	MiddleName string `json:"middle_name"`
	Email      string `json:"email" binding:"required,email"`
	Password   string `json:"password" binding:"required,min=8"`
	Phone      string `json:"phone"`
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type AuthResponse struct {
	UserID    string `json:"user_id"`
	AccountID string `json:"account_id"`
	Email     string `json:"email"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Message   string `json:"message"`
}

// SignUpHandler creates new user with profile and account
func SignUpHandler(c *gin.Context) {
	var req SignUpRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Start transaction
	tx, err := db.Begin()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}
	defer tx.Rollback()

	// 1. Create user
	var userID string
	err = tx.QueryRow(`
		INSERT INTO users (id, first_name, middle_name, last_name)
		VALUES (gen_random_uuid()::text, $1, $2, $3)
		RETURNING id
	`, req.FirstName, req.MiddleName, req.LastName).Scan(&userID)
	if err != nil {
		log.Printf("Failed to create user: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	// 2. Create profile
	_, err = tx.Exec(`
		INSERT INTO profiles (user_id, email, password_hash, phone)
		VALUES ($1, $2, $3, $4)
	`, userID, req.Email, string(hashedPassword), req.Phone)
	if err != nil {
		log.Printf("Failed to create profile: %v", err)
		// Check for unique constraint violation (duplicate email)
		if pqErr, ok := err.(*pq.Error); ok && pqErr.Code == "23505" {
			c.JSON(http.StatusConflict, gin.H{"error": "Email already registered"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create profile"})
		}
		return
	}

	// 3. Create account
	var accountID string
	err = tx.QueryRow(`
		INSERT INTO accounts (id, user_id, status, kyc_status)
		VALUES (gen_random_uuid()::text, $1, 'ACTIVE', 'NOT_STARTED')
		RETURNING id
	`, userID).Scan(&accountID)
	if err != nil {
		log.Printf("Failed to create account: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create account"})
		return
	}

	// 4. Create default "IRIS Core" portfolio
	_, err = tx.Exec(`
		INSERT INTO portfolios (account_id, name, type, is_default)
		VALUES ($1, 'Core Portfolio', 'IRIS Core', TRUE)
	`, accountID)
	if err != nil {
		log.Printf("Failed to create default portfolio: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create portfolio"})
		return
	}

	// 5. Create KYC record (empty initially)
	_, err = tx.Exec(`
		INSERT INTO kyc (account_id)
		VALUES ($1)
	`, accountID)
	if err != nil {
		log.Printf("Failed to create KYC record: %v", err)
		// Non-critical, continue
	}

	// Commit transaction
	if err = tx.Commit(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to complete signup"})
		return
	}

	c.JSON(http.StatusCreated, AuthResponse{
		UserID:    userID,
		AccountID: accountID,
		Email:     req.Email,
		FirstName: req.FirstName,
		LastName:  req.LastName,
		Message:   "Account created successfully",
	})
}

// LoginHandler authenticates user with Profile.email/password
func LoginHandler(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Query profile and user data
	var userID, firstName, lastName, passwordHash string
	var accountID sql.NullString // Allow null when no account exists yet
	err := db.QueryRow(`
		SELECT u.id, a.id, u.first_name, u.last_name, p.password_hash
		FROM profiles p
		JOIN users u ON p.user_id = u.id
		LEFT JOIN accounts a ON a.user_id = u.id
		WHERE p.email = $1
	`, req.Email).Scan(&userID, &accountID, &firstName, &lastName, &passwordHash)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}
	if err != nil {
		log.Printf("Login error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Login failed"})
		return
	}

	// Verify password
	err = bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password))
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	// Convert sql.NullString to string (empty if null)
	accountIDStr := ""
	if accountID.Valid {
		accountIDStr = accountID.String
	}

	c.JSON(http.StatusOK, AuthResponse{
		UserID:    userID,
		AccountID: accountIDStr,
		Email:     req.Email,
		FirstName: firstName,
		LastName:  lastName,
		Message:   "Login successful",
	})
}

// KYCStepHandler updates KYC information
type KYCRequest struct {
	UserID           string  `json:"user_id"`
	AccountID        string  `json:"account_id"`
	Step             int     `json:"step"`
	TaxID            string  `json:"tax_id"`
	DateOfBirth      string  `json:"date_of_birth"`
	Citizenship      string  `json:"citizenship"`
	EmploymentStatus string  `json:"employment_status"`
	AnnualIncome     float64 `json:"annual_income"`
	NetWorth         float64 `json:"net_worth"`
}

func KYCStepHandler(c *gin.Context) {
	var req KYCRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Update KYC record
	_, err := db.Exec(`
		UPDATE kyc
		SET tax_id = $1, date_of_birth = $2, citizenship = $3,
		    employment_status = $4, annual_income = $5, net_worth = $6
		WHERE account_id = $7
	`, req.TaxID, req.DateOfBirth, req.Citizenship,
		req.EmploymentStatus, req.AnnualIncome, req.NetWorth, req.AccountID)

	if err != nil {
		log.Printf("KYC update error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update KYC"})
		return
	}

	// Update account KYC status based on step
	var kycStatus string
	if req.Step >= 5 {
		kycStatus = "COMPLETED"
	} else {
		kycStatus = "IN_PROGRESS"
	}

	_, err = db.Exec(`
		UPDATE accounts
		SET kyc_status = $1
		WHERE id = $2
	`, kycStatus, req.AccountID)

	if err != nil {
		log.Printf("Account KYC status update error: %v", err)
	}

	c.JSON(http.StatusOK, gin.H{
		"step":       req.Step,
		"kyc_status": kycStatus,
		"message":    "KYC updated successfully",
	})
}

// OnboardingHandler creates Alpaca account and links to IRIS account
type OnboardingRequest struct {
	UserID      string `json:"user_id"`
	AccountID   string `json:"account_id"`
	TaxID       string `json:"tax_id"`
	DateOfBirth string `json:"date_of_birth"`
	Phone       string `json:"phone"`
	Address     string `json:"street_address"`
	City        string `json:"city"`
	State       string `json:"state"`
	PostalCode  string `json:"postal_code"`
	Country     string `json:"country"`
}

func OnboardingHandler(c *gin.Context) {
	var req OnboardingRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get user info from profiles
	var email, firstName, lastName string
	err := db.QueryRow(`
		SELECT p.email, u.first_name, u.last_name
		FROM profiles p
		JOIN users u ON p.user_id = u.id
		WHERE u.id = $1
	`, req.UserID).Scan(&email, &firstName, &lastName)

	if err != nil {
		log.Printf("Error fetching user details: %v", err)
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	// Call Broker Service to create Alpaca account
	brokerURL := os.Getenv("BROKER_SERVICE_URL")
	if brokerURL == "" {
		brokerURL = "http://iris-broker-service:8081"
	}

	alpacaReq := map[string]interface{}{
		"contact": map[string]interface{}{
			"email_address":  email,
			"phone_number":   req.Phone,
			"street_address": req.Address,
			"city":           req.City,
			"state":          req.State,
			"postal_code":    req.PostalCode,
			"country":        req.Country,
		},
		"identity": map[string]interface{}{
			"given_name":               firstName,
			"family_name":              lastName,
			"date_of_birth":            req.DateOfBirth,
			"tax_id":                   req.TaxID,
			"tax_id_type":              "USA_SSN",
			"country_of_tax_residence": "USA",
			"funding_source":           []string{"employment_income"},
		},
		"disclosures": map[string]interface{}{
			"is_control_person":               false,
			"is_affiliated_exchange_or_finra": false,
			"is_politically_exposed":          false,
			"immediate_family_exposed":        false,
		},
		"agreements": []map[string]interface{}{
			{
				"agreement":  "margin_agreement",
				"signed_at":  time.Now().Format(time.RFC3339),
				"ip_address": c.ClientIP(),
			},
			{
				"agreement":  "account_agreement",
				"signed_at":  time.Now().Format(time.RFC3339),
				"ip_address": c.ClientIP(),
			},
			{
				"agreement":  "customer_agreement",
				"signed_at":  time.Now().Format(time.RFC3339),
				"ip_address": c.ClientIP(),
			},
		},
	}

	reqBody, _ := json.Marshal(alpacaReq)
	resp, err := http.Post(brokerURL+"/v1/accounts", "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Broker Service Unavailable"})
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		c.JSON(http.StatusBadGateway, gin.H{"error": "Broker account creation failed"})
		return
	}

	var acctResp struct {
		ID            string `json:"id"`
		AccountNumber string `json:"account_number"`
	}
	json.NewDecoder(resp.Body).Decode(&acctResp)

	// Update account with Alpaca IDs
	_, err = db.Exec(`
		UPDATE accounts
		SET alpaca_account_id = $1, alpaca_account_number = $2, kyc_status = 'COMPLETED'
		WHERE id = $3
	`, acctResp.ID, acctResp.AccountNumber, req.AccountID)

	if err != nil {
		log.Printf("Failed to update account with Alpaca IDs: %v", err)
	}

	// Update profile address
	_, err = db.Exec(`
		UPDATE profiles
		SET phone = $1, address_line1 = $2, city = $3, state = $4, postal_code = $5, country = $6
		WHERE user_id = $7
	`, req.Phone, req.Address, req.City, req.State, req.PostalCode, req.Country, req.UserID)

	c.JSON(http.StatusOK, gin.H{
		"status":                "verified",
		"alpaca_account_id":     acctResp.ID,
		"alpaca_account_number": acctResp.AccountNumber,
	})
}
