# ./deps.sh # run inside of function
npm install
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
sls deploy
