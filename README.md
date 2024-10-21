# Ticket Management System

## Overview

This project is a Ticket Management System built with Flask. It allows users to create, manage, and track different types of tickets such as problem tickets, training tickets, and miscellaneous tickets. The system also includes user authentication, role-based access control, and an admin panel for managing users and tickets.

## Features

- User Authentication and Authorization
- Role-based Access Control (Admin, Teacher, Member)
- Create and Manage Problem, Training, and Miscellaneous Tickets
- Ticket History Tracking
- Admin Panel for User and Ticket Management
- Scheduled Deletion of Old Tickets
- Responsive UI with Bootstrap

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Ghoastplayer/ticket-management-system.git
    cd ticket-management-system
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```sh
    flask db upgrade
    ```

5. Run the application:
    ```sh
    flask run
    ```

## Configuration

The application configuration is stored in the `config.py` file. You can modify this file to change the database URI, secret key, and other settings.

## Usage

- **Home Page**: Displays the total number of active members.
- **Members Page**: Lists all active and inactive members.
- **Ticket Management**: Allows users to view and manage their tickets.
- **Ticket Details**: Provides detailed information about a specific ticket.
- **Admin Panel**: Allows admins to manage users and view ticket statistics.

## Scheduled Tasks

The application uses APScheduler to delete old tickets (older than 5 years) daily. This is configured in the `app/__init__.py` file.

## Security

The application uses Flask-Talisman to enforce Content Security Policy (CSP) and protect against various web vulnerabilities.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any questions or issues, please open an issue on GitHub or contact the repository owner.