FROM centos:8
USER root
RUN  yum install -y epel-release
RUN  yum -y upgrade
RUN  yum install -y python3 python3-devel git
RUN  python3 -m ensurepip
RUN  pip3 install --upgrade pip setuptools
#ENV  PYCURL_SSL_LIBRARY=openssl
RUN  pip3 install jupyterhubutils
ARG  BUILDTRIGGER="Mon Jan 27 11:32:44 MST 2020"
RUN  pip3 install \
     git+https://github.com/lsst-sqre/wfdispatcher
ENV  wf=/opt/lsst/software/workflow
ENV  verdir=${wf}/versions
RUN  mkdir -p ${verdir}
RUN  mkdir ${wf}/config ${wf}/templates
RUN  pip3 freeze > ${verdir}/requirements.txt && \
      rpm -qa | sort > ${verdir}/rpmlist.txt
ENV  LANG=C.UTF-8
RUN  groupadd -g 768 jovyan
RUN  useradd -m -g jovyan -u 768 -c "JupyterHub User" jovyan
COPY start-wf-api /usr/local/bin
USER 768:768
LABEL description="Science Platform Notebook Aspect: workflow dispatcher" \
       name="lsstsqre/wfdispatcher" \
       version="0.0.1"
CMD [ "/usr/local/bin/start-wf-api" ]
