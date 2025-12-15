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

        stage('Kubernetes Deployment') {
            steps {
                sh '''
                    kubectl cluster-info
                    sed -i "s|image: .*flask-task-manager:.*|image: irfanriaz076/flask-task-manager:${BUILD_NUMBER}|g" app-deployement.yml
                    kubectl apply -f mysql-deployement.yml
                    kubectl apply -f app-deployement.yml
                    kubectl rollout status deployment/flask-app --timeout=300s
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    kubectl get pods
                    APP_POD=$(kubectl get pod -l app=flask-app -o jsonpath="{.items[0].metadata.name}")
                    kubectl exec $APP_POD -- curl -s http://localhost:5000/health || true
                    MINIKUBE_IP=$(minikube ip || echo localhost)
                    echo "Application URL: http://$MINIKUBE_IP:30080"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f || true'
        }

        success {
            echo """
========================================
Pipeline completed successfully
========================================
Build Number: ${BUILD_NUMBER}
Docker Image: ${DOCKER_IMAGE}:${IMAGE_TAG}
========================================
"""
        }

        failure {
            echo "Pipeline failed. Check logs."
        }
    }
}
