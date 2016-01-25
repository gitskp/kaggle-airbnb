import pandas as pd
import numpy as np
from xgboost.sklearn import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import SelectFromModel
import datetime


class CustomXGB(XGBClassifier):
    """A custom XGBClassifier with feature importances computation.

    This class implements XGBClassifier and also computes feature importances
    based on the fscores. Implementing feature_importances_ property allow us
    to use `SelectFromModel` with XGBClassifier.
    """

    @property
    def feature_importances_(self):
        """Return the feature importances.

        Returns
        -------
        feature_importances_ : array, shape = [n_features]
        """
        booster = self.booster()
        fscores = booster.get_fscore()

        # TODO: Number of features?
        importances = np.zeros(x_train.shape[1])

        for k, v in fscores.iteritems():
            importances[int(k[1:])] = v

        return importances


def generate_submission(y_pred, test_users_ids, label_encoder):
    """Create a valid submission file given the predictions."""
    ids = []
    cts = []
    for i in range(len(test_users_ids)):
        idx = test_users_ids[i]
        ids += [idx] * 5
        sorted_countries = np.argsort(y_pred[i])[::-1]
        cts += label_encoder.inverse_transform(sorted_countries)[:5].tolist()

    id_stacks = np.column_stack((ids, cts))
    submission = pd.DataFrame(id_stacks, columns=['id', 'country'])

    date = datetime.datetime.now().strftime("%m-%d-%H:%M:%S")
    name = __file__.split('.')[0] + '_' + str(date) + '.csv'

    return submission.to_csv('../data/submissions/' + name, index=False)

path = '../data/processed/'
train_users = pd.read_csv(path + 'processed_train_users.csv')
test_users = pd.read_csv(path + 'processed_test_users.csv')
y_train = train_users['country_destination']
train_users.drop('country_destination', axis=1, inplace=True)
train_users.drop('id', axis=1, inplace=True)
train_users = train_users.fillna(-1)
x_train = train_users.values
label_encoder = LabelEncoder()
encoded_y_train = label_encoder.fit_transform(y_train)

test_users_ids = test_users['id']
test_users.drop('id', axis=1, inplace=True)
test_users = test_users.fillna(-1)
x_test = test_users.values


custom = CustomXGB(
    max_depth=7,
    learning_rate=0.18,
    n_estimators=80,
    gamma=0,
    min_child_weight=1,
    max_delta_step=0,
    subsample=1,
    colsample_bytree=1,
    colsample_bylevel=1,
    reg_alpha=0,
    reg_lambda=1,
    scale_pos_weight=1,
    base_score=0.5,
    missing=None,
    silent=True,
    nthread=-1,
    seed=42
)

model = SelectFromModel(custom)
model.fit(x_train, encoded_y_train)

x_new = model.transform(x_train)
x_test = model.transform(x_test)

custom.fit(x_new, encoded_y_train)
y_pred = custom.predict_proba(x_test)

generate_submission(y_pred, test_users_ids, label_encoder)