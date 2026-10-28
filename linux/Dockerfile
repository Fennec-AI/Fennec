FROM kalilinux/kali-rolling:latest

# Update and install essential pentesting tools (avoiding kali-linux-headless due to broken inetsim)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    # Core tools
    curl \
    wget \
    git \
    jq \
    unzip \
    libcap2-bin \
    ca-certificates \
    build-essential \
    pkg-config \
    # Network tools
    nmap \
    netcat-openbsd \
    dnsutils \
    whois \
    libpcap-dev \
    # Web tools
    nikto \
    gobuster \
    dirb \
    sqlmap \
    whatweb \
    wfuzz \
    # Password tools
    hydra \
    john \
    hashcat \
    # Exploitation
    exploitdb \
    commix \
    # CMS scanning
    wpscan \
    # Wordlists
    seclists \
    # Python for scripting
    python3 \
    python3-pip \
    python3-requests \
    # Go toolchain (for installing Go-based security tools)
    golang \
    # Node.js will be installed via NodeSource below
    gnupg2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure python (unversioned) resolves to python3
RUN ln -sf /usr/bin/python3 /usr/local/bin/python

# Ensure a minimal common wordlist exists even if seclists paths are missing
COPY wordlists/common.txt /usr/share/seclists/Discovery/Web-Content/common.txt

# Fix nmap execution in container - remove file capabilities that block execution
RUN setcap -r /usr/lib/nmap/nmap 2>/dev/null || true

# Go-based tools (ProjectDiscovery suite + ffuf + gospider)
ENV GOPATH=/root/go
# Prefer ProjectDiscovery's httpx over Python's unrelated httpx console script.
ENV PATH="/root/go/bin:${PATH}"
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/jaeles-project/gospider@latest && \
    go install -v github.com/ffuf/ffuf/v2@latest && \
    go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# Python-based tools
RUN pip3 install --break-system-packages --ignore-installed charset-normalizer dirsearch arjun wafw00f

# Install Node.js from NodeSource (Kali's bundled npm has an LRU constructor bug)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs

# npm-based tools (JS analysis)
RUN npm install -g js-beautify retire

# jwt_tool (JWT manipulation)
RUN rm -rf /opt/jwt_tool && rm -f /usr/local/bin/jwt_tool && \
    git clone --depth 1 https://github.com/ticarpi/jwt_tool /opt/jwt_tool && \
    pip3 install --break-system-packages -r /opt/jwt_tool/requirements.txt && \
    ln -s /opt/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool && \
    chmod +x /opt/jwt_tool/jwt_tool.py

# Set working directory
WORKDIR /work
