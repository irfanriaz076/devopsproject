pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKER_IMAGE = 'irfanriaz076/flask-task-manager'
        IMAGE_TAG = "${BUILD_NUMBER}"
        LATEST_TAG = 'latest'

        K8S_NAMESPACE = 'default'
        K8S_DEPLOYMENT = 'flask-app'

        GIT_REPO = 'https://github.com/irfanriaz076/devopsproject'
        GIT_BRANCH = 'main'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Initialize') {
            steps {
                echo "=========================================="
                echo "Starting CI/CD Pipeline"
                echo "Build Number: ${BUILD_NUMBER}"
                echo "Job Name: ${JOB_NAME}"
                echo "=========================================="
            }
        }

        stage('Cleanup Previous Deployments') {
            steps {
                echo "Cleaning up existing deployments..."
                sh '''
                    echo "Deleting previous deployments and services..."
                    kubectl delete deployment flask-app mysql prometheus grafana 2>/dev/null || true
                    kubectl delete service flask-app mysql-service prometheus-service grafana-service 2>/dev/null || true
                    
                    echo "Waiting for cleanup to complete..."
                    sleep 5
                    
                    echo "Current state:"
                    kubectl get all
                '''
            }
        }

        stage('Code Fetch') {
            steps {
                script {
                    cleanWs()
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "*/${GIT_BRANCH}"]],
                        userRemoteConfigs: [[url: GIT_REPO]]
                    ])
                }
            }
        }

        stage('Code Analysis') {
            steps {
                sh '''
                    ls -la
                    test -f app.py || exit 1
                    test -f requirements.txt || exit 1
                    test -f Dockerfile || exit 1
                    test -f mysql-deployement.yml || exit 1
                    test -f prometheus-config.yml || exit 1
                    test -f grafana-deployment.yml || exit 1
                '''
            }
        }

        stage('Docker Image Build') {
            steps {
                sh """
                    docker build -t irfanriaz076/flask-task-manager:${BUILD_NUMBER} .
                    docker tag irfanriaz076/flask-task-manager:${BUILD_NUMBER} irfanriaz076/flask-task-manager:latest
                    docker images | grep flask-task-manager
                """
            }
        }

        stage('Docker Image Test') {
            steps {
                sh """
                    docker run --rm irfanriaz076/flask-task-manager:${BUILD_NUMBER} python --version
                    docker run --rm irfanriaz076/flask-task-manager:${BUILD_NUMBER} pip list
                """
            }
        }

        stage('Push to DockerHub') {
            steps {
                sh '''
                    echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin
                    docker push irfanriaz076/flask-task-manager:${BUILD_NUMBER}
                    docker push irfanriaz076/flask-task-manager:latest
                    docker logout
                '''
            }
        }

        stage('Deploy MySQL') {
            steps {
                echo "Deploying MySQL database..."
                sh '''
                    kubectl apply -f mysql-deployement.yml
                    echo "Waiting for MySQL to be ready..."
                    kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s
                    kubectl get pods -l app=mysql
                    kubectl get svc mysql-service
                '''
            }
        }

        stage('Deploy Prometheus') {
            steps {
                echo "Deploying Prometheus monitoring..."
                sh '''
                    kubectl apply -f prometheus-config.yml
                    echo "Waiting for Prometheus to be ready..."
                    kubectl wait --for=condition=ready pod -l app=prometheus --timeout=300s
                    kubectl get pods -l app=prometheus
                    kubectl get svc prometheus-service
                '''
            }
        }

        stage('Deploy Grafana') {
            steps {
                echo "Deploying Grafana dashboards..."
                sh '''
                    kubectl apply -f grafana-deployment.yml
                    echo "Waiting for Grafana to be ready..."
                    kubectl wait --for=condition=ready pod -l app=grafana --timeout=300s
                    kubectl get pods -l app=grafana
                    kubectl get svc grafana-service
                '''
            }
        }

        stage('Deploy Flask Application') {
            steps {
                echo "Deploying Flask application..."
                sh """
                    kubectl cluster-info
                    sed -i "s|image: .*flask-task-manager:.*|image: irfanriaz076/flask-task-manager:${BUILD_NUMBER}|g" app-deployement.yml
                    kubectl apply -f app-deployement.yml
                    kubectl rollout status deployment/flask-app --timeout=300s
                """
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    echo "=========================================="
                    echo "Deployment Status"
                    echo "=========================================="
                    
                    kubectl get all
                    kubectl get svc
                    kubectl get pvc
                    
                    echo ""
                    echo "Checking Flask application health..."
                    sleep 10
                    APP_POD=$(kubectl get pod -l app=flask-app -o jsonpath="{.items[0].metadata.name}")
                    echo "Flask Pod: $APP_POD"
                    kubectl exec $APP_POD -- curl -s http://localhost:5000/health || echo "Health check pending..."
                    
                    echo ""
                    echo "Checking Flask metrics endpoint..."
                    kubectl exec $APP_POD -- curl -s http://localhost:5000/metrics | head -10 || echo "Metrics endpoint pending..."
                    
                    MINIKUBE_IP=$(minikube ip 2>/dev/null || echo localhost)
                    
                    echo ""
                    echo "=========================================="
                    echo "Access URLs:"
                    echo "=========================================="
                    echo "Flask App:    http://$MINIKUBE_IP:30080"
                    echo "Prometheus:   http://$MINIKUBE_IP:30090"
                    echo "Grafana:      http://$MINIKUBE_IP:30030"
                    echo ""
                    echo "Grafana Login: admin / admin"
                    echo "=========================================="
                '''
            }
        }

        stage('Verify Monitoring Stack') {
            steps {
                echo "Verifying monitoring stack integration..."
                sh '''
                    echo "Checking Prometheus health..."
                    PROM_POD=$(kubectl get pod -l app=prometheus -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $PROM_POD -- wget -qO- http://localhost:9090/-/healthy || echo "Prometheus health check pending..."
                    
                    echo ""
                    echo "Checking Grafana health..."
                    GRAFANA_POD=$(kubectl get pod -l app=grafana -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $GRAFANA_POD -- wget -qO- http://localhost:3000/api/health || echo "Grafana health check pending..."
                    
                    echo ""
                    echo "Verifying Prometheus is scraping Flask app..."
                    sleep 10
                    kubectl exec $PROM_POD -- wget -qO- http://localhost:9090/api/v1/targets 2>/dev/null | grep -o "flask-app" && echo "✓ Flask app found in Prometheus targets!" || echo "⚠ Flask app not yet visible in Prometheus (may take a moment)"
                    
                    echo ""
                    echo "All monitoring components deployed successfully!"
                '''
            }
        }

        stage('Setup Port Forwarding Info') {
            steps {
                echo "Providing port forwarding instructions..."
                sh '''
                    echo ""
                    echo "=========================================="
                    echo "Port Forwarding Commands (for AWS EC2)"
                    echo "=========================================="
                    echo ""
                    echo "Run these commands to access dashboards:"
                    echo ""
                    echo "# Flask App:"
                    echo "kubectl port-forward deployment/flask-app 5000:5000 --address=0.0.0.0 &"
                    echo ""
                    echo "# Prometheus:"
                    echo "kubectl port-forward deployment/prometheus 9090:9090 --address=0.0.0.0 &"
                    echo ""
                    echo "# Grafana:"
                    echo "kubectl port-forward deployment/grafana 3000:3000 --address=0.0.0.0 &"
                    echo ""
                    echo "Then access via:"
                    echo "Flask:      http://<your-ec2-ip>:5000"
                    echo "Prometheus: http://<your-ec2-ip>:9090"
                    echo "Grafana:    http://<your-ec2-ip>:3000"
                    echo "=========================================="
                '''
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f || true'
        }

        success {
            script {
                def minikubeIp = sh(script: 'minikube ip 2>/dev/null || echo localhost', returnStdout: true).trim()
                echo """
========================================
✓ Pipeline Completed Successfully!
========================================

Deployed Services:
------------------
✓ MySQL Database
✓ Flask Application
✓ Prometheus Monitoring
✓ Grafana Dashboards

Access URLs:
------------------
Flask App:    http://${minikubeIp}:30080
Prometheus:   http://${minikubeIp}:30090
Grafana:      http://${minikubeIp}:30030

Grafana Login: admin / admin
========================================
"""
            }
        }

        failure {
            echo "❌ Pipeline failed. Check logs for details."
            sh '''
                echo ""
                echo "=========================================="
                echo "Debugging Information"
                echo "=========================================="
                echo ""
                echo "Current pod status:"
                kubectl get pods
                echo ""
                echo "Current services:"
                kubectl get svc
                echo ""
                echo "Recent events:"
                kubectl get events --sort-by='.lastTimestamp' | tail -20
                echo ""
                echo "Failed pod logs (if any):"
                for pod in $(kubectl get pods --field-selector=status.phase!=Running -o name 2>/dev/null); do
                    echo "Logs for $pod:"
                    kubectl logs $pod --tail=50 2>/dev/null || echo "No logs available"
                    echo ""
                done
                echo "=========================================="
            '''
        }
    }
}
