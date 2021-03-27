#!/bin/bash

php php-cs-fixer.phar fix ./src --diff
if [ "0" != $?"" ]; then
    echo   -en '\E[31m'"$libraryCS
$testsCS\033[1m\033[0m";
    printf "\n";
    echo   -en '\E[31;47m'"\033[1mCoding standards check failed!\033[0m"   # Red
    printf "\n";
    exit   2;
fi

php php-cs-fixer.phar fix ./tests --diff
if [ "0" != $?"" ]; then
    echo   -en '\E[31m'"$libraryCS
$testsCS\033[1m\033[0m";
    printf "\n";
    echo   -en '\E[31;47m'"\033[1mCoding standards check failed!\033[0m"   # Red
    printf "\n";
    exit   2;
fi

echo   -en '\E[32m'"\033[1mCoding standards check passed!\033[0m"   # Green
printf "\n";
