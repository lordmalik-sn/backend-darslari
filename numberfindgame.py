import random
x = 10
random_son = random.randint(1, x)
tahminlar = 0

play = input('Oyin oynaymizmi? (t/f): ')
if play.lower() != 't':
    print("Keyinroq yana urinib ko'ring!")
else:
    while True:
        tahminlar += 1
        try:
            tahmin = int(input('Men bir son oyladim, topa olasizmi: '))
        except ValueError:
            print('Iltimos butun son kiriting.')
            tahminlar -= 1
            continue

        if tahmin < random_son:
            print('Men oylagan son kattaroq')
        elif tahmin > random_son:
            print('Men oylagan son kichik')
        else:
            print(f"Ha, men {tahmin} son oylagandim")
            break

    print(f"Tabriklayman {tahminlar} tahminlar bilan topdingiz")