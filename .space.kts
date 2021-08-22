job("QA and Linters") {
    parallel {
        container(displayName = "Tests", image = "python:3.9.6-bullseye") {		
            shellScript {
                    content = """
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                        /root/.poetry/bin/poetry install
                        /root/.poetry/bin/poetry run task pytest
                    """
                }
            }
            container(displayName = "Mypy", image = "python:3.9.6-bullseye") {
            shellScript {
                    interpreter = "/bin/bash"
                    content = """
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                        /root/.poetry/bin/poetry install
                        /root/.poetry/bin/poetry run task mypy
                    """
                }
            }
            container(displayName = "FlakeHell", image = "python:3.9.6-bullseye") {
            shellScript {
                    content = """
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                        /root/.poetry/bin/poetry install
                        /root/.poetry/bin/poetry run task flakehell
                    """
                }
            }
    	}
	}

sequential {
           container(displayName = "Generate data", image = "gradle:jdk11") {
               kotlinScript { api ->
                   api.gradle("generateTestData")
               }
           }
           container(displayName = "Run int tests", image = "gradle:jdk11") {
               kotlinScript { api ->
                   api.gradle("integrationTests")
               }
           }
       }

job("Build and run tests") {
    container(displayName = "Run build", image = "gradle:jdk11") {
        kotlinScript { api ->
            api.gradle("build", "-x", "test")
        }
   }

   parallel {
       container(displayName = "Run mainTests", image = "gradle:jdk11") {
           kotlinScript { api ->
               api.gradle("mainTests")
           }
       }

       sequential {
           container(displayName = "Generate data", image = "gradle:jdk11") {
               kotlinScript { api ->
                   api.gradle("generateTestData")
               }
           }
           container(displayName = "Run int tests", image = "gradle:jdk11") {
               kotlinScript { api ->
                   api.gradle("integrationTests")
               }
           }
       }
   }
}