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
                '''
            }
        }

        stage('Docker Image Build') {
            steps {
                sh '''
                    docker build -t irfanriaz076/flask-task-manager:${BUILD_NUMBER} .
                    docker tag irfanriaz076/flask-task-manager:${BUILD_NUMBER} irfanriaz076/flask-task-manager:latest
                    docker images | grep flask-task-manager
                '''
            }
        }

        stage('Docker Image Test') {
            steps {
                sh '''
                    docker run --rm irfanriaz076/flask-task-manager:${BUILD_NUMBER} python --version
                    docker run --rm irfanriaz076/flask-task-manager:${BUILD_NUMBER} pip list
                '''
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
                    kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s || true
                    kubectl get pods -l app=mysql
                '''
            }
        }

        stage('Deploy Prometheus') {
            steps {
                echo "Deploying Prometheus monitoring..."
                sh '''
                    kubectl apply -f prometheus-config.yml
                    echo "Waiting for Prometheus to be ready..."
                    kubectl wait --for=condition=ready pod -l app=prometheus --timeout=300s || true
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
                    kubectl wait --for=condition=ready pod -l app=grafana --timeout=300s || true
                    kubectl get pods -l app=grafana
                    kubectl get svc grafana-service
                '''
            }
        }

        stage('Deploy Flask Application') {
            steps {
                echo "Deploying Flask application..."
                sh '''
                    kubectl cluster-info
                    sed -i "s|image: .*flask-task-manager:.*|image: irfanriaz076/flask-task-manager:${BUILD_NUMBER}|g" app-deployement.yml
                    kubectl apply -f app-deployement.yml
                    kubectl rollout status deployment/flask-app --timeout=300s
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    echo "=========================================="
                    echo "Deployment Status"
                    echo "=========================================="
                    
                    kubectl get pods
                    kubectl get svc
                    
                    echo ""
                    echo "Checking Flask application health..."
                    APP_POD=$(kubectl get pod -l app=flask-app -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $APP_POD -- curl -s http://localhost:5000/health || true
                    
                    MINIKUBE_IP=$(minikube ip || echo localhost)
                    
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
                echo "Verifying monitoring stack..."
                sh '''
                    echo "Checking Prometheus targets..."
                    sleep 10
                    PROM_POD=$(kubectl get pod -l app=prometheus -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $PROM_POD -- wget -qO- http://localhost:9090/-/healthy || echo "Prometheus health check pending..."
                    
                    echo ""
                    echo "Checking Grafana status..."
                    GRAFANA_POD=$(kubectl get pod -l app=grafana -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $GRAFANA_POD -- wget -qO- http://localhost:3000/api/health || echo "Grafana health check pending..."
                    
                    echo ""
                    echo "All monitoring components deployed successfully!"
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
                def minikubeIp = sh(script: 'minikube ip || echo localhost', returnStdout: true).trim()
                echo """
========================================
Pipeline completed successfully
========================================
Build Number: ${BUILD_NUMBER}
Docker Image: ${DOCKER_IMAGE}:${IMAGE_TAG}

Access your services:
- Flask App:    http://${minikubeIp}:30080
- Prometheus:   http://${minikubeIp}:30090
- Grafana:      http://${minikubeIp}:30030
  (Login: admin/admin)

Next Steps:
1. Open Grafana and verify Prometheus datasource
2. Create dashboards for Flask app metrics
3. Monitor /metrics endpoint on Flask app
========================================
"""
            }
        }

        failure {
            echo "Pipeline failed. Check logs for details."
            sh '''
                echo "Current pod status:"
                kubectl get pods
                echo ""
                echo "Recent events:"
                kubectl get events --sort-by='.lastTimestamp' | tail -20
            '''
        }
    }
}    
