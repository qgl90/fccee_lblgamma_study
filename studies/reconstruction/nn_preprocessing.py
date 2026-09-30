"""Training-only preprocessing contract shared by NN fitting and inference."""

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler


class Processor:
    """Median imputation, explicit missing flags, robust scaling, clipping."""

    def __init__(self,names):
        self.names=tuple(names)
        self.imputer=SimpleImputer(strategy="median",add_indicator=True,
                                   keep_empty_features=True)
        self.scaler=RobustScaler(quantile_range=(10,90))

    def fit(self,matrix):
        self.scaler.fit(self.imputer.fit_transform(matrix.loc[:,self.names]))
        return self

    def transform(self,matrix):
        values=self.scaler.transform(self.imputer.transform(matrix.loc[:,self.names]))
        return np.clip(values,-10,10).astype("float32")
