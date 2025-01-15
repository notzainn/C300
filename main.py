import pickle as pkl

with open('data.pkl', 'rb') as file:
    data = pkl.load(file)

print(data)
