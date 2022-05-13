
from cmath import nan
import numpy as np
import pathlib
import pandas as pd
import json
import matplotlib.pyplot as plt
from typing import Union, Tuple
import copy
class QuestionnaireAnalysis:
    """
    Reads and analyzes data generated by the questionnaire experiment.
    Should be able to accept strings and pathlib.Path objects.
    """

    def __init__(self, data_fname: Union[pathlib.Path, str]):
    #    raise appropriate errors and define self.data_fname
        try:
            self.data_fname =  pathlib.Path(data_fname).resolve()
        except TypeError:
            print('file name must be either a string or a pathlib path')
            raise
        if not self.data_fname.is_file():
            raise ValueError('file does not exist, plese check directory')
        
    def read_data(self):
        """Reads the json data located in self.data_fname into memory, to
        the attribute self.data.
        """
        
        self.data= pd.read_json(self.data_fname)
        
        return self.data
        
        
    
    def show_age_distrib(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates and plots the age distribution of the participants.

    Returns
    -------
    hist : np.ndarray
    Number of people in a given bin
    bins : np.ndarray
    Bin edges
        """

        _,plot=plt.subplots()
        bin_cnt,edges,_=plot.hist(self.data['age'],bins=np.arange(0,110,10))
        plot.set_xlabel('age')
        plot.set_ylabel('counts')
        plot.set_title('age disribution')
        plt.show()
        return bin_cnt,edges
                    
    def remove_rows_without_mail(self) -> pd.DataFrame:
        """Checks self.data for rows with invalid emails, and removes them.

    Returns
    -------
    df : pd.DataFrame
    A corrected DataFrame, i.e. the same table but with the erroneous rows removed and
    the (ordinal) index after a reset.
        """
        

        # A quick trick to check for invalid emails:
        regex= r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Z|a-z]{1,}\b'
        corrected_df=self.data[self.data.email.str.match(regex)].reset_index(drop=True)
        return  corrected_df

    def fill_na_with_mean(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Finds, in the original DataFrame, the subjects that didn't answer
        all questions, and replaces that missing value with the mean of the
        other grades for that student.

    Returns
    -------
    df : pd.DataFrame
    The corrected DataFrame after insertion of the mean grade
    arr : np.ndarray
        Row indices of the students that their new grades were generated
        """    

        corrected_df = self.data.copy()
        missing_vals_idx = pd.isnull(self.data[['q1', 'q2', 'q3', 'q4', 'q5']]).any(1).to_numpy().nonzero()[0]
        new = self.data[['q1', 'q2', 'q3', 'q4', 'q5']].apply(lambda row: round(row.fillna(row.mean()), 1), axis=1)
        corrected_df[['q1', 'q2', 'q3', 'q4', 'q5']] = new

        return corrected_df, missing_vals_idx

    def score_subjects(self, maximal_nans_per_sub: int = 1) -> pd.DataFrame:
        """Calculates the average score of a subject and adds a new "score" column
        with it.

        If the subject has more than "maximal_nans_per_sub" NaN in his grades, the
        score should be NA. Otherwise, the score is simply the mean of the other grades.
        The datatype of score is UInt8, and the floating point raw numbers should be
        rounded down.

        Parameters
        ----------
        maximal_nans_per_sub : int, optional
            Number of allowed NaNs per subject before giving a NA score.

        Returns
        -------
        pd.DataFrame
            A new DF with a new column - "score".
        """
        scores_df=self.data
        # Create mean score column (type int)
        scores_df['score']=scores_df[['q1', 'q2', 'q3', 'q4', 'q5']].mean(axis=1).astype('uint8').astype('UInt8')
        # Find indices that surpass the threshold and replace with NA
        idx_to_change=scores_df[['q1', 'q2', 'q3', 'q4', 'q5']].isnull().sum(axis=1)>maximal_nans_per_sub
        scores_df.loc[idx_to_change,'score']=pd.NA
        
        return scores_df
    def correlate_gender_age(self) -> pd.DataFrame:
        """Looks for a correlation between the gender of the subject, their age
        and the score for all five questions.

    Returns
    -------
    pd.DataFrame
        A DataFrame with a MultiIndex containing the gender and whether the subject is above
        40 years of age, and the average score in each of the five questions.
    """
        gender_age_df=self.data
        # first let's get rid of nans:
        gender_age_df=gender_age_df[gender_age_df['age'].notna()] 
        # define age by above or under 40
        gender_age_df['age']=np.where(gender_age_df['age']>40,True,False)
        # set age and gender colums as index
        gender_age_df=gender_age_df.set_index(['gender','age'])
        # groupby, mean score
        mean_score_grouped=gender_age_df.groupby(['gender','age'])['q1', 'q2', 'q3', 'q4', 'q5'].mean()


        return mean_score_grouped