./IPMICFG -fru PS $1;
./IPMICFG -fru CS $2;

cd /opt/afulnx64/;
./amidelnx_26_64 /ss "$1";

./amidelnx_26_64 /cs "$2";
