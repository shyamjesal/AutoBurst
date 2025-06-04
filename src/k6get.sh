TEST_ID=`curl -s GET "https://api.k6.io/cloud/v6/load_tests" \
    -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
    -H "X-Stack-Id: 1271620" | jq ".value[0].id"`

# echo $TEST_ID

# TEST_RUN_ID=`curl -s GET "https://api.k6.io/cloud/v6/load_tests/${TEST_ID}/test_runs" \
# -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
# -H "X-Stack-Id: 1271620" | jq ".value[0].id"`

TEST_RUN_ID=`curl -s GET "https://api.k6.io/cloud/v6/load_tests/${TEST_ID}/test_runs" \
-H "Authorization: Bearer ${GRAFANA_TOKEN}" \
-H "X-Stack-Id: 1271620" | jq ".value | sort_by(.created) | reverse | .[0].id"`

# echo $TEST_RUN_ID

TIME_START=`date -d "30 seconds ago" +"%Y-%m-%dT%H:%M:%SZ"`
TIME_END=`date +"%Y-%m-%dT%H:%M:%SZ"`

# echo $TIME_START
# echo $TIME_END

curl -s GET "https://api.k6.io/cloud/v5/test_runs/${TEST_RUN_ID}/query_range_k6(query='histogram_quantile(0.95)',metric='http_req_duration',step=3,start=${TIME_START},end=${TIME_END})" \
    -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
    -H "X-Stack-Id: 1271620" | jq ".data.result[0].values | last | .[1]"
