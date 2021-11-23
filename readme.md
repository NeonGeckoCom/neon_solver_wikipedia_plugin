
Spoken answers api for wikipedia


```python
d = WikipediaSolver()
for sentence in d.spoken_answers("what is the speed of light"):
    print(sentence)
    break
    # The speed of light in vacuum, commonly denoted c, is a universal physical constant important in many areas of physics.

d = WikipediaSolver()
for sentence in d.spoken_answers("qual é a velocidade da luz", lang="pt"):
    print(sentence)
    break
    # A velocidade da luz no vácuo, comumente denotada c, é uma constante física universal importante em muitas áreas da física
```
