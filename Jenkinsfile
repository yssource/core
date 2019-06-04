pipeline {
    agent any
    stages {
        stage('Run Tests') {
            parallel {
                stage('Build On Murder') {
                    environment {
                        MACHINE = 'murder'
                        TEST_DIR= '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('murder')
                    }
                }

                stage('Build On Tx1') {
                    environment {
                        MACHINE = 'tx1'
                        TEST_DIR = '/home/jenkins/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('tx1')
                    }
                }

                stage('Build On skull-canyon') {
                    environment {
                        MACHINE = 'skull-canyon'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('skull-canyon')
                    }
                }

                stage('Build On nano') {
                        environment {
                        MACHINE = 'nano'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('nano')
                    }
                }

                stage('Build On rp-u1804s-1') {
                    environment {
                        MACHINE = 'rp-u1804s-1'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('rp-u1804s-1')
                    }
                }

                stage('Build On coral') {
                    environment {
                        MACHINE = 'coral'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('coral')
                    }
                }

                stage('Build On tx2') {
                    environment {
                        MACHINE = 'tx2'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('tx2')
                    }
                }

                stage('Build On upsquared') {
                    environment {
                        MACHINE = 'upsquared'
                        TEST_DIR = '/tmp/f0cal_profiler_test'
                    }
                    steps {
                        sh "echo ${WORKSPACE}"
                        sh "sudo salt '$MACHINE' cmd.run 'rm -rf $TEST_DIR'"
                        sh "sudo salt '$MACHINE' cmd.run 'mkdir $TEST_DIR'"
                        sh "sudo salt-cp '$MACHINE' ${WORKSPACE} $TEST_DIR --chunked"
                        sh "sudo salt '$MACHINE' cmd.run 'cd $TEST_DIR/F0cal_Mirror && python3.6 scripts/bootstrap.py -d -v _venv local -- scripts/conops'"
                    }
                    options {
                        lock('upsquared')
                    }
                }

            }
        }
    }
    post {
        always {
            checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'ci-tools']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '1039c06d-d0a0-4020-9c75-8b58139e309a', url: 'https://github.com/f0cal/ci-tools.git']]]
            sh "sudo salt '*' grains.item os osrelease kernel cpuarch --out yaml --out-file grains.yaml || true"
            sh "sudo salt '*' pkg.version python3 gcc --out yaml --out-file pkgs.yaml || true"
            sh "python3 -m venv env && env/bin/pip install -e  ci-tools"
            sh "env/bin/gen_report -g grains.yaml -p pkgs.yaml -bu 'http://192.168.1.2:8000' -pn 'F0cal_Mirror' -dn 'Build details' -s 1"
        }
    }
}
