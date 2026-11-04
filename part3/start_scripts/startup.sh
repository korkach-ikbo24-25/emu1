# stage3_startup.sh — тест всех команд этапа 3
echo $HOME
echo "user=$USER"
pwd
ls

cd /data
ls
cat a.txt
cat b.txt
cat bin.dat
pwd
cd ..
cat readme.md

# ошибки
cd /no/such/dir
ls /no/such/path
cat /no/such/file.txt
unknowncommand abc
cat "незакрытая кавычка

cd /
ls
help
