FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive
ENV WIRESHARK_INSTALL_SETUID=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    tcpdump \
    tshark \
    iproute2 \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY kali/module3/module3_kali_authorized_write.py /opt/module3/module3_kali_authorized_write.py
COPY kali/module3/entrypoint.sh /usr/local/bin/module3-kali-entrypoint

RUN chmod 755 /usr/local/bin/module3-kali-entrypoint

ENTRYPOINT ["/usr/local/bin/module3-kali-entrypoint"]
CMD ["sleep", "infinity"]
