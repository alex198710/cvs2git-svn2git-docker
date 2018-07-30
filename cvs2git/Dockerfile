# pull base image
FROM debian:jessie

MAINTAINER alexandre.fischer

ENV cvsuser user
ENV cvspass pass

ENV project test
ENV group test

ENV GITLAB_API_TOKEN token
ENV gitlabuser user
ENV gitlabpass pass

RUN apt-get update && apt-get install -y python cvs git git-cvs cvsps curl
# tofrodos
# RUN ln -s /usr/bin/fromdos /usr/bin/dos2unix

COPY ./cvs2git/cvs2git.py /
COPY ./common/common.py /
COPY ./common/.gitlab-ci.yml /
COPY ./common/sonar-project.properties /
COPY ./common/.gitignore /

RUN chmod +x /cvs2git.py
RUN chmod +x /common.py

CMD python /cvs2git.py $cvsuser $cvspass $project $group $GITLAB_API_TOKEN $gitlabuser $gitlabpass