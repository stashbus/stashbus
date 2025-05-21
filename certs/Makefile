all: ca.sscrt \
     mosquitto.server.key mosquitto.server.crt \
     stasher-mqtt.client.key stasher-mqtt.client.crt \
	 publisher-crypto.client.key publisher-crypto.client.crt \
	 publisher-brno-weather.client.key publisher-brno-weather.client.crt

%.key:
	openssl genrsa -out $@ 4096

# CA self-signed certs generation.
%.sscrt: %.key %.answ
	openssl req -new -x509 -days 3650 -key $< -out $@ -config $*.answ -extensions v3_ca

# CA signed server certs.
%.server.csr: %.server.answ %.server.key
	openssl req -new -key $*.server.key -out $@ -config $<

%.server.crt: %.server.csr %.server.cnf ca.sscrt ca.key
	openssl x509 -req -in $< -CA ca.sscrt -CAkey ca.key -out $@ -CAcreateserial -days 1 -sha256 -extfile $*.server.cnf

# CA signed client certs.
%.client.csr: %.client.answ %.client.key
	openssl req -new -key $*.client.key -out $@ -config $<

%.client.crt: %.client.csr %.client.cnf ca.sscrt ca.key
	openssl x509 -req -in $< -CA ca.sscrt -CAkey ca.key -out $@ -CAcreateserial -days 1 -sha256 -extfile $*.client.cnf


# Cleanup
clean:
	-rm *.sscrt *.csr *.crt *.key
	# podman compose up is creating the mountpoints as directories if they do not exist already, making
	# the environment unclean for make to run.
	-rmdir *.crt *.sscrt
