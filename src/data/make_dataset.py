import os
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.data import nama_lp_ulc, trng_lfs_02, tps00001

pd.options.mode.chained_assignment = None
project_dir = Path(__file__).resolve().parents[2]
data_interim_dir = os.path.join(project_dir, 'data', 'interim')


def process_dfs():
    nama_lp_ulc.process()
    trng_lfs_02.process()
    tps00001.process()


def merge_dfs():
    compensation_df = pd.read_csv(os.path.join(data_interim_dir, 'compensation.csv'))
    education_df = pd.read_csv(os.path.join(data_interim_dir, 'education.csv'))
    population_df = pd.read_csv(os.path.join(data_interim_dir, 'population.csv'))
    rd_expenditure_df = pd.read_csv(os.path.join(data_interim_dir, 'rd_expenditure.csv'))

    df = compensation_df.merge(education_df, on=['year', 'GEO'])
    df = df.merge(population_df, on=['year', 'GEO'])
    df = df.merge(rd_expenditure_df, on=['year', 'GEO'])

    df.rename(columns={
        'Compensation of employees per hour worked (Euro)': 'per_hour_worked',
        'Compensation per employee (Euro)': 'per_employee'
    }, inplace=True)

    return df


def split_dataset(df, train_size=0.7):
    years = df['year'].unique()
    years = sorted(years)
    pivot = int(len(years) * train_size)
    train_index = years[:pivot]
    test_index = years[pivot:]

    train_df = df[df['year'].isin(train_index)]
    test_df = df[df['year'].isin(test_index)]

    return train_df, test_df


def add_features(df):
    features = ['education', 'population', 'rd_expenditure']
    shift_range = [1, 2]
    for feature in features:
        for shift in shift_range:
            df[f'{feature}_shift_{shift}'] = df.sort_values('year').groupby(['GEO'])[feature].shift(shift)
            df[f'{feature}_diff_{shift}'] = df[f'{feature}_shift_{shift}'] - df[feature]

    for feature in features:
        df[f'{feature}_mean'] = df.groupby(['GEO'])[feature].transform('mean')
        df[f'{feature}_sum'] = df.groupby(['GEO'])[feature].transform('sum')


def scale_features(df):
    columns_to_fit = [
        'education_mean',
        'education_sum',
        'education_shift_1',
        'education_diff_1',
        'education_shift_2',
        'education_diff_2',
        'population_mean',
        'population_sum',
        'population_shift_1',
        'population_diff_1',
        'population_shift_2',
        'population_diff_2',
        'rd_expenditure_mean',
        'rd_expenditure_sum',
        'rd_expenditure_shift_1',
        'rd_expenditure_diff_1',
        'rd_expenditure_shift_2',
        'rd_expenditure_diff_2',
    ]

    for column in columns_to_fit:
        scaler = StandardScaler()
        df[column] = scaler.fit_transform(df[[column]])


def main():
    process_dfs()
    merged_df = merge_dfs()

    # We need to drop data unless we have a good solution to impute missing data
    merged_df = merged_df[merged_df['year'] < 2018]
    merged_df.to_csv(os.path.join(data_interim_dir, 'merged.csv'), index=False)

    train_df, test_df = split_dataset(merged_df)
    add_features(train_df)
    add_features(test_df)
    scale_features(train_df)
    scale_features(test_df)

    train_df.to_csv(os.path.join(data_interim_dir, 'train.csv'), index=False)
    test_df.to_csv(os.path.join(data_interim_dir, 'test.csv'), index=False)


if __name__ == '__main__':
    main()
