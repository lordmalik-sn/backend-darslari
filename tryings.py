T='ha'
F='yoq'
oyinchi=input(f"Oyin oynaymizmi?  {T} yoki {F}: ")
if T in oyinchi:
    import random
    tahminlar=+1
    oyinchi=int(input('Men bir son oyladim 1 va 10 orasida topingchi? '))
    kompyuter=random.randint(0,10)
    
    while True:
        
        print(kompyuter)
        if oyinchi>kompyuter:
            print(f'Men oylagan son {oyinchi} dan kichikroq')
            user=input('Xato topolmadingiz: ')
            
        elif oyinchi<kompyuter:
            print(f'Men oylagan son {oyinchi} dan kattaroq')
        else:
             break 
    print(f'Siz topdingiz {tahminlar} ta urinish bilan')

               
         
        
    
else: print('Mayli keyingi safar')

        