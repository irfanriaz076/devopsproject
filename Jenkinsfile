pipeline {
    agent any
    
    environment {
        // Docker configuration
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKER_IMAGE = "irfanriaz076/flask-task-manager"
        IMAGE_TAG = "${BUILD_NUMBER}"
        LATEST_TAG = "latest"
        
        // Kubernetes configuration
        K8S_NAMESPACE = "default"
        K8S_DEPLOYMENT = "flask-app"
        
        // Git configuration
        GIT_REPO = "https://github.com/irfanriaz076/devopsproject"
        GIT_BRANCH = "main"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    stages {
        stage('Initialize') {
            steps {
                script {
                    echo "=========================================="
                    echo "Starting CI/CD Pipeline"
                    echo "Build Number: ${BUILD_NUMBER}"
                    echo "Build ID: ${BUILD_ID}"
                    echo "Job Name: ${JOB_NAME}"
                    echo "=========================================="
                }
            }
        }
        
        stage('Code Fetch') {
            steps {
                echo 'Stage 1: Fetching code from GitHub...'
                script {
                    try {
                        // Clean workspace
                        cleanWs()
                        
                        // Checkout code from GitHub
                        checkout([
                            $class: 'GitSCM',
                            branches: [[name: "*/${GIT_BRANCH}"]],
                            userRemoteConfigs: [[url: "${GIT_REPO}"]]
                        ])
                        
                        echo 'Code fetched successfully!'
                        
                        // Display git information
                        sh '''
                            echo "Git Commit: $(git rev-parse HEAD)"
                            echo "Git Author: $(git log -1 --pretty=format:'%an')"
                            echo "Git Message: $(git log -1 --pretty=format:'%s')"
                        '''
                    } catch (Exception e) {
                        error "Failed to fetch code: ${e.message}"
                    }
                }
            }
        }
        
        stage('Code Analysis') {
            steps {
                echo 'Stage 2: Performing code analysis...'
                script {
                    try {
                        // List project structure
                        sh '''
                            echo "Project Structure:"
                            ls -la
                            
                            echo "\nChecking for required files..."
                            if [ -f "app.py" ]; then
                                echo "✓ app.py found"
                            else
                                echo "✗ app.py not found"
                                exit 1
                            fi
                            
                            if [ -f "requirements.txt" ]; then
                                echo "✓ requirements.txt found"
                            else
                                echo "✗ requirements.txt not found"
                                exit 1
                            fi
                            
                            if [ -f "Dockerfile" ]; then
                                echo "✓ Dockerfile found"
                            else
                                echo "✗ Dockerfile not found"
                                exit 1
                            fi
                        '''
                        
                        echo 'Code analysis completed!'
                    } catch (Exception e) {
                        error "Code analysis failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Docker Image Creation') {
            steps {
                echo 'Stage 3: Building Docker image...'
                script {
                    try {
                        // Build Docker image with both tags
                        sh """
                            echo "Building Docker image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                            docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                            docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:${LATEST_TAG}
                            
                            echo "Verifying image..."
                            docker images | grep ${DOCKER_IMAGE}
                        """
                        
                        echo ' Docker image built successfully!'
                    } catch (Exception e) {
                        error " Docker image creation failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Docker Image Testing') {
            steps {
                echo 'Stage 4: Testing Docker image...'
                script {
                    try {
                        sh """
                            echo "Testing Docker image..."
                            docker run --rm ${DOCKER_IMAGE}:${IMAGE_TAG} python --version
                            docker run --rm ${DOCKER_IMAGE}:${IMAGE_TAG} pip list
                            
                            echo "Image size:"
                            docker images ${DOCKER_IMAGE}:${IMAGE_TAG} --format "{{.Size}}"
                        """
                        
                        echo 'Docker image tested successfully!'
                    } catch (Exception e) {
                        error "Docker image testing failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Push to DockerHub') {
            steps {
                echo 'Stage 5: Pushing Docker image to DockerHub...'
                script {
                    try {
                        // Login to DockerHub
                        sh """
                            echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                        """
                        
                        // Push both tags
                        sh """
                            echo "Pushing ${DOCKER_IMAGE}:${IMAGE_TAG}"
                            docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                            
                            echo "Pushing ${DOCKER_IMAGE}:${LATEST_TAG}"
                            docker push ${DOCKER_IMAGE}:${LATEST_TAG}
                        """
                        
                        echo 'Docker image pushed successfully!'
                        echo "Image available at: https://hub.docker.com/r/${DOCKERHUB_CREDENTIALS_USR}/flask-task-manager"
                    } catch (Exception e) {
                        error "Failed to push Docker image: ${e.message}"
                    } finally {
                        // Logout from DockerHub
                        sh 'docker logout'
                    }
                }
            }
        }
        
        stage('Kubernetes Deployment') {
            steps {
                echo 'Stage 6: Deploying to Kubernetes...'
                script {
                    try {
                        // Check Kubernetes connectivity
                        sh '''
                            echo "Checking Kubernetes cluster..."
                            kubectl cluster-info
                            kubectl get nodes
                        '''
                        
                        // Update image in deployment
                        sh """
                            # Update the deployment YAML with new image tag
                            sed -i 's|image: .*flask-task-manager:.*|image: irfanriaz076/flask-task-manager:${BUILD_NUMBER}|g' app-deployement.yml

                        """
                        
                        // Apply MySQL deployment first
                        sh '''
                            echo "Deploying MySQL..."
                            kubectl apply -f mysql-deployement.yml
                            
                            echo "Waiting for MySQL to be ready..."
                            kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s || true
                            kubectl get pods -l app=mysql
                        '''
                        
                        // Apply application deployment
                        sh '''
                            echo "Deploying Flask application..."
                            kubectl apply -f app-deployement.yml
                            
                            echo "Waiting for deployment rollout..."
                            kubectl rollout status deployment/flask-app --timeout=300s
                        '''
                        
                        // Verify deployment
                        sh '''
                            echo "\n=== Deployment Status ==="
                            kubectl get deployments
                            
                            echo "\n=== Pods Status ==="
                            kubectl get pods -o wide
                            
                            echo "\n=== Services Status ==="
                            kubectl get services
                            
                            echo "\n=== PVC Status ==="
                            kubectl get pvc
                        '''
                        
                        echo 'Kubernetes deployment successful!'
                    } catch (Exception e) {
                        // Show logs on failure
                        sh '''
                            echo "Deployment failed. Showing pod logs..."
                            kubectl get pods
                            kubectl describe pods -l app=flask-app
                            kubectl logs -l app=flask-app --tail=50 || true
                        '''
                        error "Kubernetes deployment failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Prometheus/Grafana Stage') {
            steps {
                echo 'Stage 7: Setting up monitoring...'
                script {
                    try {
                        // Deploy Prometheus
                        sh '''
                            echo "Deploying Prometheus..."
                            kubectl apply -f prometheus-config.yml
                            
                            echo "Waiting for Prometheus to be ready..."
                            kubectl wait --for=condition=ready pod -l app=prometheus --timeout=120s || true
                        '''
                        
                        // Deploy Grafana
                        sh '''
                            echo "Deploying Grafana..."
                            kubectl apply -f grafana-deployement.yml
                            
                            echo "Waiting for Grafana to be ready..."
                            kubectl wait --for=condition=ready pod -l app=grafana --timeout=120s || true
                        '''
                        
                        // Show monitoring endpoints
                        sh '''
                            echo "\n=== Monitoring Services ==="
                            kubectl get svc prometheus-service grafana-service
                            
                            MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "localhost")
                            echo "\nPrometheus URL: http://${MINIKUBE_IP}:30090"
                            echo "Grafana URL: http://${MINIKUBE_IP}:30030"
                            echo "Grafana Credentials - Username: admin, Password: admin"
                        '''
                        
                        echo 'Monitoring setup completed!'
                    } catch (Exception e) {
                        echo "Warning: Monitoring setup encountered issues: ${e.message}"
                        echo "Pipeline will continue..."
                    }
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo 'Stage 8: Verifying complete deployment...'
                script {
                    try {
                        sh '''
                            echo "=== Final Verification ==="
                            
                            # Check all pods are running
                            echo "\n1. Pod Status:"
                            kubectl get pods --all-namespaces
                            
                            # Check services
                            echo "\n2. Service Status:"
                            kubectl get svc
                            
                            # Test application endpoint
                            echo "\n3. Testing Application Health:"
                            APP_POD=$(kubectl get pod -l app=flask-app -o jsonpath="{.items[0].metadata.name}")
                            kubectl exec $APP_POD -- curl -s http://localhost:5000/health || echo "Health check pending..."
                            
                            # Get application URL
                            MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "localhost")
                            echo "\n4. Application Access:"
                            echo "Application URL: http://${MINIKUBE_IP}:30080"
                            echo "Prometheus URL: http://${MINIKUBE_IP}:30090"
                            echo "Grafana URL: http://${MINIKUBE_IP}:30030"
                            
                            # Resource usage
                            echo "\n5. Resource Usage:"
                            kubectl top nodes || echo "Metrics not available yet"
                            kubectl top pods || echo "Metrics not available yet"
                        '''
                        
                        echo 'Deployment verification completed!'
                    } catch (Exception e) {
                        echo "Verification warning: ${e.message}"
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            script {
                // Clean up Docker images
                sh '''
                    echo "Cleaning up old Docker images..."
                    docker system prune -f || true
                    docker images
                '''
            }
        }
        
        success {
            echo """
            ========================================
                Pipeline completed successfully!
            ========================================
            Build Number: ${BUILD_NUMBER}
            Docker Image: ${DOCKER_IMAGE}:${IMAGE_TAG}
            
            Access your application:
            - Application: http://\$(minikube ip):30080
            - Prometheus: http://\$(minikube ip):30090
            - Grafana: http://\$(minikube ip):30030
            ========================================
            """
        }
        
        failure {
            echo """
            ========================================
                   Pipeline failed!
            ========================================
            Build Number: ${BUILD_NUMBER}
            Check the logs above for error details.
            ========================================
            """
            
            // Collect diagnostic information
            script {
                sh '''
                    echo "Collecting diagnostic information..."
                    kubectl get all
                    kubectl describe pods -l app=flask-app || true
                    kubectl logs -l app=flask-app --tail=100 || true
                '''
            }
        }
        
        unstable {
            echo 'Pipeline completed with warnings'
        }
        
        aborted {
            echo 'Pipeline was aborted'
        }
    }
}
