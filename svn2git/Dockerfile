# pull base image
FROM debian:jessie

MAINTAINER alexandre.fischer

ENV svnuser user
ENV svnpass pass
ENV svnroot SVN_URL

ENV trunkbase null
ENV branchesbase null
ENV tagsbase null

ENV project test
ENV group test
ENV nobranches False
ENV notags False
ENV processTagsAsBranches False

ENV GITLAB_API_TOKEN token
ENV gitlabuser user
ENV gitlabpass pass
ENV gitlabproject null

RUN apt-get update && apt-get install -y python git curl subversion git-svn xmlstarlet
# tofrodos
# RUN ln -s /usr/bin/fromdos /usr/bin/dos2unix

COPY ./svn2git/svn2git.py /
COPY ./common/common.py /
COPY ./svn2git/servers /root/.subversion/servers
COPY ./common/.gitlab-ci.yml /
COPY ./common/sonar-project.properties /
COPY ./common/.gitignore /

RUN chmod +x /svn2git.py
RUN chmod +x /common.py

CMD python /svn2git.py $svnuser $svnpass $project $group $GITLAB_API_TOKEN $gitlabuser $gitlabpass $svnroot $trunkbase $branchesbase $tagsbase $nobranches $notags $processTagsAsBranches $gitlabproject