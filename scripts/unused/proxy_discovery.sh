#!/usr/bin/sh
auto_find_proxy() {
    if [ -f last_moment.hosts ]; then
        rm last_moment.hosts
    fi

    if [ -f new_host.hosts ]; then
        rm new_host.hosts
    fi

    cps host-list | awk '/440BX Desktop Reference Platform/ { print $2 }' > last_moment.hosts

    for ((i=1; i<11; i++)); 
    do
        echo "time="${i}
        sleep 10s
        for host in `cps host-list | awk '/440BX Desktop Reference Platform/ { print $2 }'`;
        do
            #echo "host : "${host}
            result=`cat last_moment.hosts | grep ${host}`
            if [ "${result}" == "" ]; then
                #echo "this is new host."
                echo ${host} > new_host.hosts
                return 0
            fi
        done
    done
    echo "error" > new_host.hosts
    return 1
}

config_proxy() {
    proxt_name=$1
    proxy_host=`cat new_host.hosts`
    echo "after 20s exe cps command, proxy_host="${proxy_host}

	sleep 20s
    cps role-host-add --host ${proxy_host} dhcp
    cps commit

    for (( i=1; i<5; i++ ));
    do
        echo "check proxy status, time="${i}
        sleep 5s
        temp=`cps host-list | grep ${proxy_host} |  awk -F '|' '{ print $4 }'`
        temp=${temp//' '/''}
        if [ "${temp}" == "" ]; then
             echo "wait..."
        else
             echo "success" > auto_add_proxy.result
             return 0
        fi
    done
	echo "error" > auto_add_proxy.result
    return 1
}


check() {
    if [ ! -f auto_add_proxy.result ]; then
        exit 1
    fi

    add_resutl=`cat auto_add_proxy.result`

    if [ "${add_resutl}" == "success" ]; then
	    proxy_host=`cat new_host.hosts`
		echo ${proxy_host}
	    exit 0
	else
	    exit 1
    fi
}

if [ "$1" == "check" ]; then
    check
fi

auto_find_proxy
if [ "$?" = 0 ]; then
    config_proxy $1
else
    echo "error" > auto_add_proxy.result
fi