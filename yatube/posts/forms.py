from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].label = 'Группа'
        self.fields['group'].empty_label = '-Выберите группу-'
        self.fields['text'].label = 'Текст поста'
        self.fields['text'].help_text = 'Текст нового поста'
        self.fields['group'].help_text = ('Группа, '
                                          'к которой будет относиться пост')

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
