# VSCodeでは、launch.jsonに追加済。F5で実行できる
#!/bin/bash
docker run --rm -it\
    -v $PWD:/data\
    -u $(id -u):$(id -g) openjournals/inara\
    -o pdf,crossref paper.md