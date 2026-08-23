from django.db import models


class Play(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'plays'
        managed = False

    def __str__(self):
        return self.name


class Character(models.Model):
    id = models.BigAutoField(primary_key=True)
    play = models.ForeignKey(Play, on_delete=models.DO_NOTHING, db_column='play_id')
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'characters'
        managed = False

    def __str__(self):
        return self.name


class Scene(models.Model):
    id = models.BigAutoField(primary_key=True)
    play = models.ForeignKey(Play, on_delete=models.DO_NOTHING, db_column='play_id')
    act = models.BigIntegerField()
    scene = models.BigIntegerField()

    class Meta:
        db_table = 'scenes'
        managed = False

    def __str__(self):
        return f'{self.play.name} - Act {self.act}, Scene {self.scene}'


class Speech(models.Model):
    id = models.BigAutoField(primary_key=True)
    play = models.ForeignKey(Play, on_delete=models.DO_NOTHING, db_column='play_id')
    character = models.ForeignKey(Character, on_delete=models.DO_NOTHING, db_column='character_id')
    scene_ref = models.ForeignKey(Scene, on_delete=models.DO_NOTHING, db_column='scene_id')
    act = models.BigIntegerField()
    scene = models.BigIntegerField()
    start_line = models.BigIntegerField()
    end_line = models.BigIntegerField()
    text = models.TextField()

    class Meta:
        db_table = 'speeches'
        managed = False

    def __str__(self):
        return f'{self.character.name} ({self.start_line}-{self.end_line})'
