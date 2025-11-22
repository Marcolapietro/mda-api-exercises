# API Documentation with Swagger/OpenAPI
## Practical Exercise: Library System

### 📚 Introduction

This exercise is designed to learn the fundamentals of API documentation using Swagger/OpenAPI 3.0. Through a practical library system case, we will learn to document endpoints, define data models, and establish security parameters.

### 🎯 Learning Objectives

- Understand the basic structure of an OpenAPI 3.0 document
- Learn to document endpoints with different HTTP methods
- Define data models using schemas
- Implement authentication and security
- Practice documenting responses and status codes
- Use the Swagger editor to validate specifications

### 🛠️ Required Tools

1. **Text editor** (recommended):
   - Visual Studio Code
   - Sublime Text
   - WebStorm

2. **Online tools**:
   - [Swagger Editor](https://editor.swagger.io)
   - [Swagger UI](https://swagger.io/tools/swagger-ui/)

### 📝 Reference Examples

#### 1. Basic OpenAPI Structure

```yaml
openapi: 3.0.0
info:
  title: Example API
  version: 1.0.0
  description: A simple API to understand the basic structure

servers:
  - url: http://api.example.com/v1
    description: Production server
  - url: http://staging.example.com/v1
    description: Staging server

paths:
  /hello:
    get:
      summary: Basic greeting
      description: Returns a greeting message
      responses:
        '200':
          description: Successful greeting
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: "Hello, world!"
```

#### 2. Endpoint with Parameters

```yaml
paths:
  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
          description: User ID
          example: 123
        - in: query
          name: include
          schema:
            type: string
          description: Additional fields to include
          example: "profile,preferences"
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          example: 123
        name:
          type: string
          example: "John Doe"
        email:
          type: string
          example: "john@example.com"
```

#### 3. POST Operation with Request Body

```yaml
paths:
  /products:
    post:
      summary: Create new product
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                  example: "Gaming Laptop"
                price:
                  type: number
                  format: float
                  example: 999.99
                category:
                  type: string
                  enum: ["electronics", "clothing", "food"]
                  example: "electronics"
              required:
                - name
                - price
                - category
      responses:
        '201':
          description: Product created successfully
        '400':
          description: Invalid data
```

### 📋 Main Exercise: Library API

#### Base Specification

```yaml
openapi: 3.0.0
info:
  title: Library API
  version: 1.0.0
  description: Library management system

servers:
  - url: http://localhost:3000
    description: Development server

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY

  schemas:
    Book:
      type: object
      properties:
        id:
          type: string
          example: "book123"
        title:
          type: string
          example: "Don Quixote"
        author:
          type: string
          example: "Miguel de Cervantes"
        isbn:
          type: string
          example: "978-84-376-0494-7"
        availableQuantity:
          type: integer
          example: 5
        category:
          type: string
          example: "Classic Literature"
      required:
        - title
        - author
        - isbn
```

#### Endpoints to Document

1. **Book Management**:
   - GET /books
   - GET /books/{id}
   - POST /books
   - PUT /books/{id}
   - DELETE /books/{id}

2. **Loan Management**:
   - POST /loans
   - GET /loans
   - PUT /loans/{id}/return
   - GET /loans/user/{userId}

### ✅ Exercise Tasks

1. **Basic Documentation**
   - Complete the basic API information
   - Configure servers
   - Implement security scheme

2. **Book Endpoints**
   - Document all book endpoints
   - Include necessary parameters
   - Define possible responses

3. **Loan Endpoints**
   - Create schema for loans
   - Document CRUD operations
   - Include validations

4. **Additional Enhancements**
   - Implement pagination
   - Add search filters
   - Document rate limiting


### 📝 Deliverables

1. Complete `openapi.yaml` file
2. Screenshots from Swagger editor showing validation
3. Design decisions document (optional)

### 🚫 Common Errors to Avoid

1. **Syntax**
   - Incorrect indentation
   - Missing quotes in special strings
   - Misspelled references

2. **Design**
   - Forgetting to document errors
   - Not including examples
   - Incomplete schemas

3. **Validation**
   - Not verifying in Swagger editor
   - Ignoring warnings
   - Not testing examples

### 💡 Development Tips

1. **Start Simple**
   - Begin with a basic endpoint
   - Validate frequently
   - Add complexity gradually

2. **Documentation**
   - Use clear descriptions
   - Include realistic examples
   - Maintain consistency

3. **Testing**
   - Validate in Swagger editor
   - Test different cases
   - Verify references

### 🔍 Additional Resources

1. **Official Documentation**
   - [OpenAPI Specification](https://swagger.io/specification/)
   - [Swagger Tools](https://swagger.io/tools/)

2. **Tools**
   - [Swagger Editor](https://editor.swagger.io)
   - [OpenAPI Generator](https://openapi-generator.tech)

3. **Tutorials**
   - [Swagger Tutorial](https://swagger.io/docs/specification/basic-structure/)
   - [OpenAPI Best Practices](https://swagger.io/blog/api-best-practices/)

### 🤔 Frequently Asked Questions

1. **How do I validate my YAML?**
   - Use online Swagger editor
   - Check indentation
   - Verify references

2. **How do I organize my schemas?**
   - Group by functionality
   - Use references
   - Maintain consistency

3. **How do I document errors?**
   - Include all possible status codes
   - Provide error examples
   - Explain common causes


