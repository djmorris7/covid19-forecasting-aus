#!/bin/bash
#SBATCH -p batch
#SBATCH --qos=express
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=00:30:00
#SBATCH --mem=20GB
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=sophie.schiller@adelaide.edu.au

module load arch/haswell
module load Python/3.6.1-foss-2016b
source ../virtualenvs/bin/activate

python collate_states.py $1 $2 $3
python analysis/record_to_csv.py $1 $2 R_L $3

deactivate