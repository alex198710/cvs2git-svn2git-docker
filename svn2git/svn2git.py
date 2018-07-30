#!/usr/bin/python
import sys
import os
import re
import json
import time
import common

svnuser = None
svnpass = None
svnroot = None

trunkbase = None
branchesbase = None
tagsbase = None

project = None 
group = None
gitlaburl = None
GITLAB_API_TOKEN = None
gitlabproject = None

nobranches = False
notags = False
processTagsAsBranches = False

authorsFile = "/authors.txt"
trustCerts = " --trust-server-cert --non-interactive "

# FIELDS TO SET
prodBranch = "PROD"
domainEmail = "@example.com"
authorizedBranches = [prodBranch, "master"] # branches not renamed yet

def initArgs():
	global svnuser, svnpass, svnroot, project, group, GITLAB_API_TOKEN, gitlaburl, trunkbase, branchesbase, tagsbase, nobranches, notags, processTagsAsBranches, gitlabproject
	
	svnuser = sys.argv[1];
	print("svnuser: " + svnuser)
	svnpass = sys.argv[2];
	print("svnpass: " + svnpass)
	
	project = sys.argv[3]
	print("project: " + project)
	
	group = sys.argv[4]
	print("group: " + group)
	
	GITLAB_API_TOKEN = sys.argv[5]
	print("GITLAB_API_TOKEN: " + GITLAB_API_TOKEN)
	
	gitlabuser = sys.argv[6]
	gitlabpass = sys.argv[7]
	common.GITLAB_API_TOKEN = GITLAB_API_TOKEN
	
	svnroot = sys.argv[8]
	print("svnroot: " + svnroot)
	
	if sys.argv[9] != "null":
		trunkbase = sys.argv[9]
	else: 
		trunkbase = "trunk/" + project
	print("trunkbase: " + trunkbase)
	
	if sys.argv[10] != "null":
		branchesbase = sys.argv[10]
	else: 
		branchesbase = "branches/" + project
	print("branchesbase: " + branchesbase)
	
	if sys.argv[11] != "null":
		tagsbase = sys.argv[11]
	else: 
		tagsbase = "tags/" + project
	print("tagsbase: " + tagsbase)
	
	if sys.argv[12] == 'True':
		nobranches = True
	print("nobranches: " + str(nobranches))
	
	if sys.argv[13] == 'True':
		notags =  True
	print("notags: " + str(notags))
	
	if sys.argv[14] == 'True':
		processTagsAsBranches = True
	print("processTagsAsBranches: " + str(processTagsAsBranches))
	
	if sys.argv[15] != "null":
		gitlabproject = sys.argv[15]
	else: 
		gitlabproject = project
	print("gitlabproject: " + gitlabproject)
	
	gitlaburl = "https://" + gitlabuser + ":" + gitlabpass + "@" + common.GITLAB_BASE_URL + "/" + group + "/" + gitlabproject + ".git"
	print("gitlaburl: " + gitlaburl)
	
def svn2git(rev):
	print("===> Launching migration SVN to GIT for project " + project)
	print(common.executeCommand("pwd"))
	revision = "" 
	if rev is not None and rev != "":
		revision = "--revision " + rev + ":HEAD"
	
	basecommand = "git svn clone " + revision + " --no-minimize-url -T " + trunkbase + " -A " + authorsFile + " --username=" + svnuser + " " + svnroot + " " + project
	
	# first attempt to accept certificate on the prompt
	command = "echo 'p' | " + basecommand
	print(command)
	os.system(command)
	
	# second attempt to put password on the prompt
	command = "echo '" + svnpass + "' | " + basecommand
	print(command)
	os.system(command)

def getFirstRevision(repoWithCreds):
	rev = common.executeCommand("svn log -r 1:HEAD --limit 1 --xml " + trustCerts + repoWithCreds + ' | xmlstarlet sel -t -v "/log/logentry/@revision" -c "." | ' + "cut -d'<' -f1 | xargs").strip().split(' ')[0]
	print("===> First revision: " + rev)
	return rev
	
def extractAuthors(repoWithCreds, deleteFile):
	command="svn log -q  " + trustCerts + repoWithCreds + " | grep -e '^r' --binary-files=text | awk 'BEGIN { FS = " + '"|"' + " } ; { print $2 }' | sort | uniq"
	authorsInLog = common.executeCommand(command).splitlines()
	print(authorsInLog)
	
	if deleteFile == True and os.path.isfile(authorsFile):
		os.remove(authorsFile)

	for line in authorsInLog:
		author = line.strip()
		refactoredAuthor = author + "=" + author + "<" + author + domainEmail + ">\n"
		with open(authorsFile, "a") as f:
			#print(refactoredAuthor)
			f.write(refactoredAuthor)

def uniqAuthors():
	uniqAuthors = []
	for line in open(authorsFile):
		uniqAuthors.append(line)
	uniqAuthors = sorted(set(uniqAuthors))
	os.remove(authorsFile)
	for line in uniqAuthors:
		with open(authorsFile, "a") as f:
			f.write(line)
	

def migrateBranches():
	print("===> Migrate branches")
	
	branchList = common.executeCommand("svn list " + svnroot + "/" + branchesbase + " | sed 's/\///'").splitlines()
	nbBranches = len(branchList)
	print("Found : " + str(nbBranches) + " branches")
	
	if nbBranches > 0:
		print(branchList)
		
		for branch in  branchList:
			repoWithCreds = svnroot + "/" + branchesbase + "/" + branch + "/" + project + " --username " + svnuser + " --password " + svnpass
			extractAuthors(repoWithCreds, False)
			
		uniqAuthors()
		
		common.executeCommand("git config --add svn-remote.svn.branches " + branchesbase + "/*/" + project + ":refs/remotes/origin/*")
		common.executeCommand("git svn fetch")
		#common.executeCommand("git svn fetch") # executed two times because it can remain something
		#common.executeCommand("git remote update") # tweak for branches that cannot be checkout "did not match any file known to git"
		#common.executeCommand("git fetch") # tweak for branches that cannot be checkout "did not match any file known to git"
		
		print("==> Final authors file")
		for line in open(authorsFile, "r"):
			print(line)
	
		for branch in  branchList:
			common.executeShell("git checkout " + branch)
			if branch in authorizedBranches:
				common.addMandatoryFiles(project)

		common.changeBranches("master", "old_trunk")
		common.changeBranches(prodBranch, "master")
		common.createDevelop()

		common.pushAll()

	return branchList

def migrateTags(branchList):
	#common.executeCommand("git checkout develop")
	if processTagsAsBranches == False:
		if branchList is not None and len(branchList) > 0:
			print("===> Recreate tags")
			for branch in branchList:
				try:
					common.executeShell("git checkout " + branch)
					branchRegex = branch[:-1]
					common.reTag(branchRegex)
				except:
					print("An error occurred while migrating tag: " + branch + str(sys.exc_info()[0]))
			common.pushTags()
	else:
		print("===> Migrate tags")
		tagsList = common.executeCommand("svn list " + svnroot + "/" + tagsbase + " | sed 's/\///'").splitlines()
		
		nbTags = len(tagsList)
		print("Found : " + str(nbTags) + " tags")
		if nbTags > 0:
			print(tagsList)
			for tag in  tagsList:
				try:
					version=common.executeCommand("svn info " + svnroot + "/" + tagsbase + "/" + tag + "/" + project + " | grep 'Last Changed Rev' | sed 's/Last Changed Rev: //'").strip()
					if len(version) > 0:
						commit=common.executeCommand("git log --format='%h %b' | grep " + version + " | cut -c1-7").strip()
						if len(commit) > 0:
							common.executeCommand("git tag -a " + tag + " "  + commit + ' -m "' + tag + '"')

				except:
					print("An error occurred while migrating tag: " + tag + str(sys.exc_info()[0]))
			common.pushTags()
	
def main():
	initArgs()
	projectId = common.checkParameters(group, gitlabproject)
	repoWithCreds = svnroot + "/" + trunkbase + " --username " + svnuser + " --password " + svnpass
	rev = getFirstRevision(repoWithCreds)
	extractAuthors(repoWithCreds, True)

	svn2git(rev)

	common.changeDirectory(project)
	common.initGit(svnuser, svnuser+domainEmail, project, gitlaburl)

	branchList = None
	if nobranches == False:
		branchList = migrateBranches()
		
	if notags == False:
		migrateTags(branchList)

	common.pushToGitlab()
	common.setupProject(projectId)
	#common.cleanWorkspace(project)
	
start_time = time.time()
main()
print("--- %s minutes ---" % (int(time.time() - start_time)/60))