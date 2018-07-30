#!/usr/bin/python
import sys
import os
import re
import json
import shutil
from subprocess import PIPE, Popen


#project = None 
#group = None
#gitlaburl = None
#folder = None
GITLAB_API_TOKEN = None

GITLAB_BASE_URL = "gitlab.example.com"
GITLAB_API="https://" + GITLAB_BASE_URL + "/api/v4/"

def checkParameters(group, project):
	groupId = None
	
	groupObj = getGroup(group)
	if groupObj is not None:
		groupId = str(groupObj["id"])
	else:
		groupId = createGroup(group)
		
	projectId = projectExists(project, group);
	if (projectId is None):
		projectId = createProject(project, groupId)
	return projectId
		
def groupExists(group):
	groupObj = getGroup(group)
	if groupObj is not None:
		print("Group id : " + str(groupObj["id"]))
		return True
	else:
		print("No result")
		return False
		
def projectExists(project, group):
	projectObj = getProject(project)
	if projectObj is not None and projectObj["namespace"]["name"] == group:
		print("Project id : " + str(projectObj["id"]))
		return str(projectObj["id"])

	print("No result")
	return None
		
def getGroup(group):
	print("Get group name: " + group)
	ret = callGitlabApi("groups?search=" + group)
	print(ret)
	groups = json.loads(ret)
	for g in groups:
		if g["name"] == group:
			print(g)
			return g
	return None
	
def getProject(project):
	projects = json.loads(callGitlabApi("projects?search=" + project))
	for p in projects:
		if p["name"] == project:
			print(p)
			return p
	return None

def createGroup(group):
	groupObj = json.loads(callGitlabApi(
		"groups",
		' -H "Content-Type: application/json" -X POST -d ',
		"'{\"name\":\"" + group + "\",\"path\":\"" + group + "\", \"visibility\":\"internal\"}' "
	))
	id = str(groupObj["id"])
	print("Group created with Id: " + id)
	return id
	
def createProject(project, groupId):
	projectObj = json.loads(callGitlabApi(
		"projects",
		' -H "Content-Type: application/json" -X POST -d ',
		"'{\"name\":\"" + project + "\",\"path\":\"" + project + "\", \"visibility\":\"internal\", \"namespace_id\":\"" + groupId + "\"}' "
	))
	id = str(projectObj["id"])
	print("Project created with Id: " + id)
	return id

def deleteGroup(group):
	groupObj = getGroup(group)
	if groupObj is not None:
		id = str(groupObj["id"])
		print("Group " + group + " with id " + id + " is going to be deleted")
		callGitlabApi("groups/" + id, " -X DELETE ")
	else:
		print("Group does not exists")
		
def deleteProject(project):
	projectObj = getProject(project)
	if projectObj is not None:
		id = str(projectObj["id"])
		print("Project " + project + " with id " + id + " is going to be deleted")
		callGitlabApi("projects/" + id, " -X DELETE ")
	else:
		print("Project does not exists")

def setupProject(projectId):
	json.loads(callGitlabApi(
		"projects/" + projectId,
		' -H "Content-Type: application/json" -X PUT -d ',
		"'{\"id\":\"" + projectId + "\",\"default_branch\":\"develop\",\"only_allow_merge_if_pipeline_succeeds\":\"true\",\"only_allow_merge_if_all_discussions_are_resolved\":\"true\",\"build_allow_git_fetch\":\"false\"}' "
	))
	json.loads(callGitlabApi(
		"projects/" + projectId + "/protected_branches",
		' -H "Content-Type: application/json" -X POST -d ',
		"'{\"id\": \"" + projectId + "\", \"name\": \"develop\" }' "
	))
	json.loads(callGitlabApi(
		"projects/" + projectId + "/protected_branches",
		' -H "Content-Type: application/json" -X POST -d ',
		"'{\"id\": \"" + projectId + "\", \"name\": \"V15_*\" }' "
	))
	json.loads(callGitlabApi(
		"projects/" + projectId + "/protected_branches",
		' -H "Content-Type: application/json" -X POST -d ',
		"'{\"id\": \"" + projectId + "\", \"name\": \"V16_*\" }' "
	))

def callGitlabApi(apiPath, header = "", params = ""):
	url = "curl --silent --header \"Private-Token: " + GITLAB_API_TOKEN + "\" " + header + params + GITLAB_API + apiPath
	print(url)
	pop = os.popen(url)
	ret = pop.read()
	pop.close()
	return ret

def createDirectory(project):
	os.system("mkdir " + project)
	print("===> Creating directory " + project)
	
def changeDirectory(directory):
	os.chdir(directory)
	print("===> Changing directory to " + directory + ". We are now at: " + os.getcwd())
	
def execCmd(cmd):
	print(cmd)
	os.system(cmd)

def initGit(username, email, projectName, gitlaburl):
	execCmd("git config --global user.email " + email)
	execCmd("git config --global user.name " + username)
	execCmd("git config --global core.autocrlf false")
	#display autocrlf
	execCmd("git config --global core.autocrlf")
	setGitlabUrl(gitlaburl)
	addMandatoryFiles(projectName)
	
def addMandatoryFiles(projectName):
	execCmd("find . -name \".cvsignore\" -exec rm {} \;")
	execCmd("find . -name \".svnignore\" -exec rm {} \;")
	execCmd("find . -name \".project\" -exec rm {} \;")
	execCmd("rm .classpath")
	execCmd("cp ../.gitignore .")
	execCmd("cp ../.gitlab-ci.yml .")
	execCmd("cp ../sonar-project.properties .")
	execCmd("sed -i 's/PROJECT_NAME/"+projectName+"/' sonar-project.properties")
	execCmd("git add '*.cvsignore'")
	execCmd("git add '*.svnignore'")
	execCmd("git add '*.project'")
	execCmd('git add .classpath')
	execCmd('git add .gitignore')
	execCmd('git add .gitlab-ci.yml')
	execCmd('git add sonar-project.properties')
	execCmd('git commit -m "add .gitignore, .gitlab-ci.yml and sonar-project.properties files"')
	# replace CRLF by LF
	# execCmd('find ./src -type f -exec dos2unix {} \;')
	# execCmd('git commit -am "renormalize files in order to use LF as EOL"')
	
def pushToGitlab():
	pushAll()
	pushTags()

def setGitlabUrl(gitlaburl):
	print("===> Pushing to remote gitlab server : " + gitlaburl)
	execCmd("git remote add origin " + gitlaburl)

def pushAll():
	execCmd("git push --all")

def pushTags():
	execCmd("git push --tags")

def cleanWorkspace(project):
	print("===> Cleaning workspace")
	if os.path.isdir(project):
		shutil.rmtree(project)

def executeCommand(command):
	print(command)
	return executeShell(command)

def executeShell(command):
	process = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True)
	(out, err) = process.communicate()
	if err is not None:
		print(err)
	return out

def changeBranches(sourceBranch, destBranch):
	print("Renaming branch: " + sourceBranch + " to: " + destBranch)
	executeShell("git checkout " + sourceBranch)
	executeShell("git checkout -b " + destBranch)
	executeShell("git branch -D " + sourceBranch)

def createDevelop():
	print("Creating develop branch")
	executeShell("git checkout master && git pull")
	executeShell("git checkout -b develop")
	executeShell("find . -name \"pom.xml\" -exec sed -i s/-TEST/-SNAPSHOT/ {} \;")
	executeShell("git add '*pom.xml'")
	executeShell('git commit -m "Change version from -TEST to -SNAPSHOT"')

def branchExists(branchName):
	command = "git branch -a | grep '" + branchName + "' ; echo $?"
	process = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True)
	(out, err) = process.communicate()
	res = out
	if err is not None and err.strip() != '':
		res = err + res
	return res.splitlines().pop()

def tagExists(branchName):
	command = "git show-ref --tags | grep '" + branchName + "' ; echo $?"
	process = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True)
	(out, err) = process.communicate()
	res = out
	if err is not None and err.strip() != '':
		res = err + res
	return res.splitlines().pop()

def reTag(branchRegex):
	tagsList = executeCommand('git log --pretty=oneline | grep "released version ' + branchRegex + '"' + " | sed 's/ .*released version /,/' | sed 's/ .*//'").splitlines()
	nbTags = len(tagsList)
	print("Found : " + str(nbTags) + " tags")
	if nbTags > 0:
		print(tagsList)
		for tag in tagsList:
			commit = tag[0:7]
			tagSplitted = tag.split(",")
			if len(tagSplitted) > 1:
				version = tagSplitted[1]
				executeCommand("git tag -a " + version + " "  + commit + ' -m "' + version + '"')
	