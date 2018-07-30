#!/usr/bin/python
import sys
import os
import smtplib
import json
import time
import common
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

server = None
cvsuser = None
cvsroot = None
project = None 
group = None
gitlaburl = None
gitlabuser = None
GITLAB_API_TOKEN = None


# FIELDS TO SET
CVS_URL = "@example.com:/path/to/cvs_repository"
oldTrunkBranch = "old_trunk"
domainEmail = "@example.com"
prodBranch = "PROD"
RELEASE_BRANCHES = [] # Array of maintained releases branches

def initArgs():
	global cvsuser, cvsroot, project, group, GITLAB_API_TOKEN, gitlaburl, gitlabuser
	cvsuser = sys.argv[1];
	cvspass = sys.argv[2];
	cvsroot = ":pserver:" + cvsuser + ":" + cvspass + CVS_URL
	print("cvsroot: " + cvsroot)
	
	project = sys.argv[3]
	print("project: " + project)
	
	group = sys.argv[4]
	print("group: " + group)
	
	GITLAB_API_TOKEN = sys.argv[5]
	print("GITLAB_API_TOKEN: " + GITLAB_API_TOKEN)
	
	gitlabuser = sys.argv[6]
	gitlabpass = sys.argv[7]
	gitlaburl = "https://" + gitlabuser + ":" + gitlabpass + "@" + common.GITLAB_BASE_URL + "/" + group + "/" + project + ".git"
	print("gitlaburl: " + gitlaburl)

	common.GITLAB_API_TOKEN = GITLAB_API_TOKEN

def declareCvsRoot(cvsroot):
	print("===> Set the CVS root server")
	os.system("CVSROOT=" + cvsroot + " cvs login")

def cvs2git(cvsroot, project):
	print("===> Launching migration CVS to GIT for project " + project)
	common.executeShell("git cvsimport -v -R -d" + cvsroot + " " + project)

def initServer():
	global server
	server = smtplib.SMTP('smtp.travelsoft.fr', 25)
	#server.starttls()
	#server.login("YOUR EMAIL ADDRESS", "YOUR PASSWORD")

def sendMail(body):
	mailfrom = "migration-git" + domainEmail
	mailto = [gitlabuser + domainEmail]
	msg = MIMEMultipart()
	msg['From'] = mailfrom
	msg['To'] = ", ".join(mailto)
	msg['Subject'] = "CVS to GIT migration Report : " + project
	msg.attach(MIMEText(body, 'plain'))
	server.sendmail(mailfrom, mailto, msg.as_string())

def compareCvsGit(cvsroot, gitlaburl, branchList):
	initServer()
	msg = "Report branch by branch\n"
	for branch in  branchList:
		msg += "\n################## " + branch + " ##################\n"
		common.executeShell("git clone " + gitlaburl + " git-" + branch)
		common.changeDirectory("git-" + branch)
		common.executeShell("git checkout " + branch)
		common.changeDirectory("..")
		
		cvsbranch = prodBranch if branch == "master" else branch
		cvsbranch = "trunk" if branch == oldTrunkBranch else cvsbranch
		common.executeShell("cvs -q -d " + cvsroot + " co " + ("" if cvsbranch == "trunk" else (" -r " + cvsbranch)) + " -d cvs-" + cvsbranch + " " + project)
		
		diffbrief = common.executeShell("diff --brief -r -d -w git-" + branch + " cvs-" + cvsbranch + " | grep -v CVS")
		difflong = common.executeShell("diff -r -d -w git-" + branch + " cvs-" + cvsbranch + " | grep -v CVS")

		msg += diffbrief + "\n" + difflong
		msg += "\n######################################################\n"
	sendMail(msg)
	server.quit()

def main():
	initArgs()
	projectId = common.checkParameters(group, project)
	declareCvsRoot(cvsroot)
	common.createDirectory(project)
	common.changeDirectory(project)
	
	cvs2git(cvsroot, project)
	# in branch master=> old_trunk
	common.initGit(cvsuser, cvsuser+'@orchestra.eu', project, gitlaburl)
	common.executeCommand("git branch -d origin")
	#common.pushToGitlab(gitlaburl)

	branchProdExists = common.branchExists(prodBranch)
	print("===> Branch PROD exists: " + str(branchProdExists))
	
	if (branchProdExists):
		common.changeBranches("master", oldTrunkBranch)
		
		# in branch PROD => master
		common.changeBranches(prodBranch, "master")
		common.addMandatoryFiles(project)
	
	common.createDevelop()

	if (branchProdExists):
		branchList = RELEASE_BRANCHES
		for branch in  branchList:
			common.executeShell("git checkout " + branch)
			common.addMandatoryFiles(project)
			common.reTag(branch)

	common.pushToGitlab()
	common.setupProject(projectId)

	if (branchProdExists):
		compareCvsGit(cvsroot, gitlaburl, RELEASE_BRANCHES + ["master", oldTrunkBranch])
	else:
		compareCvsGit(cvsroot, gitlaburl, ["master", oldTrunkBranch])

	#common.cleanWorkspace(project)

start_time = time.time()
main()
print("--- %s minutes ---" % (int(time.time() - start_time)/60))