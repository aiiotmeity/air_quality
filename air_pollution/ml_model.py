import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime, timedelta

# Define target columns (without spaces)
target_columns = ['PM25', 'PM10', 'NO', 'NO2', 'NOX', 'NH3', 'SO2', 'CO', 'O3']


def prepare_data(df):
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
    df.columns = df.columns.str.strip()
    df['day'] = df['Date'].dt.day
    df['month'] = df['Date'].dt.month
    df['day_of_week'] = df['Date'].dt.dayofweek
    return df


def create_sequences(data, target_cols, lookback=7):
    X, y = [], []
    dates = []
    for i in range(len(data) - lookback):
        sequence = data.iloc[i:i + lookback][target_cols].values
        target = data.iloc[i + lookback][target_cols].values
        dates.append(data.iloc[i + lookback]['Date'])
        X.append(sequence)
        y.append(target)
    return np.array(X), np.array(y), dates


def train_model(df):
    df = prepare_data(df)
    X, y, dates = create_sequences(df, target_columns, lookback=7)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {}
    accuracies = {}

    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }

    for i, col in enumerate(target_columns):
        rf = RandomForestRegressor(random_state=42)
        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, scoring='r2', n_jobs=-1)
        grid_search.fit(X_train.reshape(X_train.shape[0], -1), y_train[:, i])

        best_model = grid_search.best_estimator_
        models[col] = best_model

        y_pred = best_model.predict(X_test.reshape(X_test.shape[0], -1))

        mse = mean_squared_error(y_test[:, i], y_pred)
        r2 = r2_score(y_test[:, i], y_pred)
        accuracies[col] = {'RMSE': np.sqrt(mse), 'R2': r2}

    return models, accuracies, X, y, dates


def forecast_next_days(models, last_sequence, last_date, n_days=4):
    forecasts = []
    forecast_dates = []
    current_sequence = last_sequence.copy()
    current_date = last_date

    for i in range(n_days):
        day_forecast = []
        next_date = current_date + timedelta(days=1)
        forecast_dates.append(next_date)

        for col in target_columns:
            sequence_reshaped = current_sequence.reshape(1, -1)
            pred = models[col].predict(sequence_reshaped)[0]
            day_forecast.append(pred)

        current_sequence = np.roll(current_sequence, -1, axis=0)
        current_sequence[-1] = day_forecast
        forecasts.append(day_forecast)
        current_date = next_date

    forecast_df = pd.DataFrame(forecasts, columns=target_columns)
    forecast_df.insert(0, 'Date', forecast_dates)
    return forecast_df