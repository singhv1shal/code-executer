from django.db import models

from enum import Enum
# Create your models here.

class ChoiceEnum(Enum):

    @classmethod
    def choices(cls):
        return [(x.name,x.value) for x in cls] 

class SubmissionStatus(ChoiceEnum):
    NT = 'NOT TESTED'
    RE = 'RUNTIME ERROR'
    TLE = 'TIME LIMIT EXCEEDED'
    AC = 'ACCEPTED'
    WA = 'WRONG ANSWER'
    CE = 'COMPILE ERROR'

class Language(ChoiceEnum):
    C = 'GNU C'
    CPP = 'GNU C++'
    JAVA = 'JAVA'
    PYTHON3 = 'PYTHON3'
    PYTHON2 = 'PYTHON2'

class TestCase(models.Model):
    input_text = models.TextField(default="")

class Submission(models.Model):
    submitter = models.CharField(max_length = 50, null=True,blank=True)
    status = models.CharField(max_length = 10, default = "NT", choices = SubmissionStatus.choices())
    language = models.CharField(max_length = 10, default = "C", choices = Language.choices())
    code = models.TextField(default="")
    output = models.TextField(default="")
    created = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default = True)