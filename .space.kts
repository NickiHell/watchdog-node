/**
* JetBrains Space Automation
* This Kotlin-script file lets you automate build activities
* For more info, see https://www.jetbrains.com/help/space/automation.html
*/
job("Tests") {
    container(displayName = "Tests", image = "ubuntu")
    shellScript {
            content = """
                ls
                echo World!
            """
        }
    startOn {
        gitPush {
            branchFilter {
                +"refs/heads/main"
            }
            pathFilter {
                -"**/MyFile.kt"
            }
        }
    }
}