#!/bin/bash
#SBATCH -p batch
#SBATCH --qos=express
#SBATCH -N 1
#SBATCH -n 4
#SBATCH --time=1-00:00:00
#SBATCH --mem=20GB
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=dennis.liu01@adelaide.edu.au

module load Python/3.6.1-foss-2016b
source $FASTDIR/virtualenvs/bin/activate


#dates=("2020-04-01" "2020-04-08" "2020-04-15" "2020-04-22" "2020-04-29" "2020-05-06" 
#"2020-05-13" "2020-05-20" "2020-05-27" "2020-06-03" "2020-06-10" "2020-06-17" "2020-06-24" 
#"2020-07-01" "2020-07-08" "2020-07-15" "2020-07-22")

python analysis/cprs/generate_posterior.py $1
python analysis/cprs/generate_RL_forecasts.py $1

deactivate
