#!/usr/bin/env bash
ip route show | grep 172.16.2.0/24 && ip route del 172.16.2.0/24
ip route show | grep 172.28.64.0/24 && ip route del 172.28.64.0/24
let i=0
until ip route show | grep 172.16.2.0/24
do
  ip route add 172.16.2.0/24 via 162.3.141.253
  sleep 1s
  echo add external api route, sleep $i
  ((i++==6000)) && exit
done
let i=0
until ip route show | grep 172.28.64.0/24
do
  ip route add 172.28.64.0/24 via 192.28.48.253
  sleep 1s
  echo add external api route, sleep $i
  ((i++==6000)) && exit
done
ip route show table external_api | grep 172.16.2.0/24 && ip route del table external_api 172.16.2.0/24
ip route add table external_api 172.16.2.0/24 via 162.3.141.253
