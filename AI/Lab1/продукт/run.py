import pickle
import numpy as np
class ModelExecutor:
    def __init__(self, model_path='clf.pkl'):
        self.model_path = model_path
        self.model = pickle.load(open(self.model_path, 'rb'))
    def predict(self, mode, input: np.ndarray = np.asarray([[5.1,3.5,1.4,0.2], [7.0,3.2,4.7,1.4]])):
        if mode == 'Hello':
            return 'Hello'
        else:
            return self.model.predict(input)
if __name__ == '__main__':
    print('Что-нибудь')
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--model_path', required=False, default='clf.pkl', type=str, help='Path to model file')
    parser.add_argument('--mode', required=True, type=str, help='auto or Hello')

    args = parser.parse_args()

    me = ModelExecutor(model_path=args.model_path)
    print(me.predict(mode=args.mode))