pipeline {
    agent any

    environment {
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        IMAGE_NAME = 'gns3-deploy'
    }

    stages {

        /*
         * Jenkins automatically checks out the gns3-project-deploy repository
         * before entering the stages below.
         */

        stage('Checkout Course Code') {
            when {
                expression {
                    return params.PROJECT_ID == '480-2'
                }
            }

            steps {
                echo "📚 Project 480-2 detected. Checking out private course repository..."

                dir('course-config') {
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']],
                        userRemoteConfigs: [[
                            url: 'https://github.com/kunkelec-stack/it-ot-security-course.git',
                            credentialsId: 'it-ot-security-course'
                        ]],
                        extensions: [[
                            $class: 'CloneOption',
                            depth: 1,
                            noTags: true,
                            shallow: true
                        ]]
                    ])
                }

                sh '''
                    echo "🔎 Verifying course deployment files..."

                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/deploy-gns3-course.py

                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_1_wastewater_flat.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_2_freshwater_baseline.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_3_traffic_modbus.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_4_manufacturing_risk.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_5_grid_purdue_segmented.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_6_rail_purdue_monitoring.json
                    test -f course-config/course_it_ot_convergence/gns3_water_treatment/configs/module_7_capstone_purdue_template.json

                    echo "✅ Private course repository checked out successfully."
                    echo "✅ All seven module configuration files found."
                '''
            }
        }

        stage('Checkout Code') {
            steps {
                /*
                 * Keep the existing generic deployment checkout.
                 * This works for ALL projects.
                 */
                git url: "${GITHUB_URL}",
                    branch: 'main',
                    credentialsId: 'Backstage-GNS3-Project-Deploy'
            }
        }

        stage('Update Deployment Files') {
            steps {
                script {
                    writeFile file: 'datastore', text: "${params.DATASTORE}"
                    writeFile file: 'project-id', text: "${params.PROJECT_ID}"

                    echo "📝 Updated deployment files:"
                    echo "   - Datastore: ${params.DATASTORE}"
                    echo "   - Project ID: ${params.PROJECT_ID}"
                    echo "   - Target IP: ${params.IP_ADDRESS}"

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'Backstage-GNS3-Project-Deploy',
                            usernameVariable: 'GIT_USERNAME',
                            passwordVariable: 'GIT_PASSWORD'
                        )
                    ]) {
                        sh """
                            git config user.email "jenkins@miamioh.edu"
                            git config user.name "Jenkins CI"

                            git add datastore project-id

                            git diff --staged --quiet || \
                            git commit -m "Deploy project ${params.PROJECT_ID} to datastore ${params.DATASTORE} (IP: ${params.IP_ADDRESS})"

                            git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/miamioh-cit/gns3-project-deploy.git main
                        """
                    }
                }
            }
        }

        stage('Build Docker Image (No Cache)') {
            steps {
                script {
                    echo "🐳 Building Docker image..."

                    sh "docker builder prune -f || true"

                    sh "docker build --no-cache -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Run GNS3 Deployment in Docker') {
            steps {
                script {
                    echo "🚀 Running GNS3 deployment..."

                    sh """
                        docker run --rm \
                          -e GNS3_URL=http://${params.IP_ADDRESS}:80 \
                          -e GNS3_USER=gns3 \
                          -e GNS3_PASSWORD=gns3 \
                          ${IMAGE_NAME}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ GNS3 Project ${params.PROJECT_ID} Deployed Successfully to ${params.IP_ADDRESS}!"
        }

        failure {
            echo "❌ GNS3 Project Deployment Failed!"
        }
    }
}
