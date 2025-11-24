# Team Project: API for Project and Task Management

## **Context: Business Case**

Your team has been hired by a fictional company, **ProManage**, that needs a solution to manage projects and work teams. The company requires an API that allows registering projects, assigning team members, managing tasks, and controlling permissions based on user roles.

### **Project Objective**

Develop a RESTful API that allows **ProManage** to:
1. Register users and assign them roles (`admin`, `manager`, `developer`).
2. Create projects and assign a team to each project.
3. Create tasks associated with a project, assign them to team members, and control their status.
4. Restrict access to certain routes based on user roles:
   - **Admin:** Can manage everything.
   - **Manager:** Can manage projects and tasks for their team.
   - **Developer:** Can update tasks assigned to them.

---

## **Exercise Requirements**

### **Roles and Permissions**
- **Admin:**
  - Create and delete users.
  - Assign roles to users.
  - View all projects and tasks.
- **Manager:**
  - Create projects.
  - Assign users to projects.
  - Create and assign tasks to team members.
- **Developer:**
  - View assigned tasks.
  - Update the status of their tasks (`To Do`, `In Progress`, `Done`).

### **Data Structure**
- **Users:**
  - `id`, `username`, `password`, `role`
- **Projects:**
  - `id`, `name`, `manager_id`, `team` (list of `user_id`)
- **Tasks:**
  - `id`, `project_id`, `assigned_to`, `description`, `status`

---

## **Instructions**

### **1. Team Formation**
Form teams of 3 to 5 members. Each member will assume a responsibility, such as:
- Designing the data structure.
- Implementing endpoints.
- Configuring roles and permissions.
- Testing the API.

### **2. Technical Requirements**
- Use **Flask**, **JWT**, and **Flask-Principal** for authentication and permission control.
- Implement pagination for listing projects and tasks.
- Make sure to handle errors and return clear responses in the API.

### **3. Required Endpoints**

#### **Users**
- **POST /register:** Register a user with an assigned role.
- **POST /login:** Authenticate a user and return a JWT token.
- **GET /users:** (Admin) List all users.

#### **Projects**
- **POST /projects:** (Manager/Admin) Create a new project.
- **GET /projects:** (All roles) List projects visible to the user.
- **PUT /projects/<id>:** (Manager/Admin) Update project information.
- **DELETE /projects/<id>:** (Admin) Delete a project.

#### **Tasks**
- **POST /projects/<id>/tasks:** (Manager/Admin) Create a task for a project.
- **GET /projects/<id>/tasks:** (All roles) List project tasks.
- **PUT /tasks/<id>:** (Developer) Update the status of a task assigned to the user.
- **DELETE /tasks/<id>:** (Manager/Admin) Delete a task.

---

## **Evaluation Criteria**

1. **Functionality:** Endpoints work as expected.
2. **Security:** Roles and permissions are implemented correctly.
3. **Organization:** Code is structured and easy to understand.
4. **Collaboration:** All team members participate in development.

---

## **Steps for the Team**

1. **Planning:**
   - Define the API structure and divide responsibilities.
2. **Development:**
   - Implement endpoints and test each one's functionality.
3. **Testing:**
   - Use Postman to verify workflows.
   - Ensure role restrictions are handled correctly.
4. **Documentation:**
   - Write a README file explaining how to use the API.
   - Include examples of requests and responses.

---

## **Deliverables**
1. API source code.
2. A detailed README file with usage instructions.
3. A brief report explaining how you divided the work and resolved problems.

---

Good luck developing this solution for **ProManage**!
