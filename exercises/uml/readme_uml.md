# Practice: UML Sequence Diagrams

## Introduction
This material will help you understand and practice creating UML sequence diagrams. Sequence diagrams are a fundamental tool for visualizing interactions between system components.

## Basic Concepts

### Main Elements
1. **Actors**: Represent users or external systems
2. **Participants**: Represent systems, services, or components
3. **Messages**: Arrows indicating communication between participants
4. **Lifelines**: Vertical lines representing time

### Message Types
- **Synchronous**: Solid arrow with filled head (→)
- **Response**: Dotted arrow with open head (-->)
- **Asynchronous**: Dotted arrow with filled head (-->)

## Basic Examples

### Example 1: Simple Login
```
actor User
participant System

User->>System: login(username, password)
System-->>User: loginSuccessful
```

This example shows:
- An actor (User)
- A system
- A simple request
- A response

### Example 2: Database Query
```
actor User
participant System
participant Database

User->>System: searchProduct(id)
System->>Database: query(id)
Database-->>System: productData
System-->>User: displayProduct
```

This example shows:
- Multiple participants
- Message chain
- Data flow

## Advanced Features

### Loops
```
loop For each item in cart
    User->>System: addToCart(item)
    System-->>User: itemAdded
end
```

### Conditions
```
alt stock available
    System->>Database: updateStock()
    Database-->>System: stockUpdated
else stock not available
    System-->>User: stockError
end
```

### Parallel Processes
```
par Parallel processes
    System->>EmailService: sendNotification()
    System->>System: updateStatistics()
end
```

## Practical Exercises

### Exercise 1: Basic Components
Create a sequence diagram showing:
- A user registering in the system
- The system validating the data
- A success or error response

### Exercise 2: Database Interaction
Design a diagram representing:
- A user searching for a product by ID
- The system querying a database
- Handling cases when the product exists and when it doesn't exist

### Exercise 3: Checkout Process
Create a diagram for a checkout process that includes:
- Cart verification
- Stock validation
- Order creation

### Exercise 4: Notification System
Design a diagram showing:
- A main synchronous process
- Asynchronous notification sending
- Multiple services interacting

## Evaluation Criteria
- Correct use of UML syntax
- Clarity in representing interactions
- Appropriate handling of alternative flows
- Proper use of advanced features when necessary

## Additional Resources
- [Official UML Documentation](https://www.uml.org/)
- [Sequence Diagram Guide](https://www.visual-paradigm.com/guide/uml-unified-modeling-language/what-is-sequence-diagram/)
- Recommended tools for UML diagrams:
  - [PlantUML](https://plantuml.com/)
  - [Draw.io](https://draw.io/)
  - [Lucidchart](https://www.lucidchart.com/)

## Submission
- Diagrams must be submitted in image format or in a file compatible with the mentioned tools
- Include a brief description of each diagram
