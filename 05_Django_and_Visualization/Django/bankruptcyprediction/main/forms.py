from django import forms

class searchForm(forms.Form):
    company_name = forms.CharField(label='', max_length=20)
    company_name.widget.attrs.update({'placeholder': '기업이름을 입력하세요'})
    company_name.widget.attrs.update({'class': 'searchTerm'})