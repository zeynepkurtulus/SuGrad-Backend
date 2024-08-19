# SuGrad-Backend

The SuGrad backend is a core component of the SuGrad project, an academic advising platform developed to enhance course selection and graduation planning for students at Sabancı University. The backend is built using FastAPI and MongoDB, providing robust, scalable, and efficient services that power the platform’s core functionalities, including personalized course recommendations, academic planning tools, and user management.

## Features

- FastAPI Framework: Utilizes FastAPI, a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It supports asynchronous programming, which enhances performance and scalability.
- MongoDB Integration: Employs MongoDB, a NoSQL database, to manage large volumes of academic data, including detailed student profiles, course catalogs, and academic records, ensuring flexibility and scalability.
- Personalized Course Recommendations: Implements sophisticated algorithms that analyze a student’s academic history, preferences, and goals to provide tailored course suggestions. These recommendations are designed to align with individual academic trajectories and career aspirations.
- Secure Authentication: Implements JWT (JSON Web Tokens) for secure authentication and authorization, ensuring that user data remains protected during interactions with the platform.
- Containerization: The backend services are containerized using Docker, ensuring consistent development, testing, and production environments, which facilitates easy deployment and scaling.
- CI/CD Pipeline: Integrated with GitHub Actions for continuous integration and deployment, automating the build, test, and deployment processes to ensure rapid and reliable delivery of new features and updates.

## Installation

- Clone the repository: git clone https://github.com/zeynepkurtulus/SuGrad-Backend.git
- Navigate to the project directory: cd SuGrad-Backend
- Build and run the Docker containers: docker-compose up --build
- The backend API will be accessible at http://95.214.177.119

## API Documentation
- API documentation is provided through Swagger, which can be accessed at: http://95.214.177.119/docs
- This interface allows you to explore and test the API endpoints directly.

## Contributing

We welcome contributions to improve SuGrad! Please fork the repository, create a feature branch, and submit a pull request with a detailed description of your changes.

