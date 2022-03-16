# Make file to process all python scripts in this directory
# working directory
survey_year = 2022eng
survey_version = 22.4
target_pdf_normal = ict_survey_$(survey_year)_v$(survey_version).pdf
target_pdf_review = ict_survey_$(survey_year)_v$(survey_version)_review.pdf
target_pdf_zzp = ict_survey_$(survey_year)_v$(survey_version)_zzp.pdf
target_pdf_dtc = ict_survey_$(survey_year)_v$(survey_version)_dtc.pdf

SURVEY_MAKER = survey_maker
settings = ict_survey.yml

# define all  dependencies
depends = $(settings)

# doe *make debug="--debug" om het debug argument via de command line toe te voegen
options = --write_log --log_file_debug  $(debug) #
dtc_options = --color dtc --prune_color --no_color alleengrotebedrijven
zzp_options = --color zzp --prune_color --no_color alleengrotebedrijven

tex_extensions = .tex .sdaps .xdv
err_extensions = .err .out
rest_files = code128.tex sdaps.cls

all: survey_pdf_normal survey_pdf_review survey_pdf_dtc survey_pdf_zzp

default: all

# hiermee cleanen we alles behalve de PDF output file
clean_normal: 	clean_survey_pdf_normal clean_tex_survey_pdf_normal clean_log_survey_pdf_normal
clean_review: 	clean_survey_pdf_review clean_tex_survey_pdf_review clean_log_survey_pdf_review
clean_dtc: 	clean_survey_pdf_dtc clean_tex_survey_pdf_dtc clean_log_survey_pdf_dtc
clean_zzp: 	clean_survey_pdf_zzp clean_tex_survey_pdf_zzp clean_log_survey_pdf_zzp
clean: 	clean_normal clean_review clean_zzp clean_dtc clean_rest

# hiermee cleanen we alles inclusief de PDF output file
cleanall: clean_all_normal clean_all_review clean_all_dtc clean_all_zzp clean

.PHONY: default all cleanall

survey_pdf_normal: $(target_pdf_normal)
$(target_pdf_normal): $(depends)
	$(SURVEY_MAKER) $(settings) $(options) --log_file_base log_$(target_pdf_normal:.pdf=)
clean_survey_pdf_normal:
	@$(foreach file, $(target_pdf_normal), test -f $(file) && latexmk -c $(file:.pdf=) || echo No $(file);)
clean_all_normal:
	@$(foreach file, $(target_pdf_normal), test -f $(file) && latexmk -C $(file:.pdf=) || echo No $(file);)
clean_tex_survey_pdf_normal:
	$(foreach ext, $(tex_extensions), $(foreach file, $(target_pdf_normal:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)
clean_log_survey_pdf_normal:
	$(foreach ext, $(err_extensions), $(foreach file, log_$(target_pdf_normal:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)

# survey review maken
survey_pdf_review: $(target_pdf_review)
$(target_pdf_review): $(depends)
	$(SURVEY_MAKER) --review $(settings) $(options) --log_file_base log_$(target_pdf_review:.pdf=)

# survey review schoonmaken
clean_survey_pdf_review:
	@$(foreach file, $(target_pdf_review), test -f $(file) && latexmk -c $(file:.pdf=) || echo No $(file);)
clean_all_review:
	@$(foreach file, $(target_pdf_review), test -f $(file) && latexmk -C $(file:.pdf=) || echo No $(file);)
clean_tex_survey_pdf_review:
	$(foreach ext, $(tex_extensions), $(foreach file, $(target_pdf_review:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)
clean_log_survey_pdf_review:
	$(foreach ext, $(err_extensions), $(foreach file, log_$(target_pdf_review:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)

# survey dtc maken
survey_pdf_dtc: $(target_pdf_dtc)
$(target_pdf_dtc): $(depends)
	$(SURVEY_MAKER)  $(settings) $(options) $(dtc_options) --log_file_base log_$(target_pdf_dtc:.pdf=)

# survey dtc schoonmaken
clean_survey_pdf_dtc:
	@$(foreach file, $(target_pdf_dtc), test -f $(file) && latexmk -c $(file:.pdf=) || echo No $(file);)
clean_all_dtc:
	@$(foreach file, $(target_pdf_dtc), test -f $(file) && latexmk -C $(file:.pdf=) || echo No $(file);)
clean_tex_survey_pdf_dtc:
	$(foreach ext, $(tex_extensions), $(foreach file, $(target_pdf_dtc:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)
clean_log_survey_pdf_dtc:
	$(foreach ext, $(err_extensions), $(foreach file, log_$(target_pdf_dtc:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)

# survey zzp maken
survey_pdf_zzp: $(target_pdf_zzp)
$(target_pdf_zzp): $(depends)
	$(SURVEY_MAKER) $(settings) $(options) $(zzp_options) --log_file_base log_$(target_pdf_zzp:.pdf=)

# survey zzp schoonmaken
clean_survey_pdf_zzp:
	@$(foreach file, $(target_pdf_zzp), test -f $(file) && latexmk -c $(file:.pdf=) || echo No $(file);)
clean_all_zzp:
	@$(foreach file, $(target_pdf_zzp), test -f $(file) && latexmk -C $(file:.pdf=) || echo No $(file);)
clean_tex_survey_pdf_zzp:
	$(foreach ext, $(tex_extensions), $(foreach file, $(target_pdf_zzp:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)
clean_log_survey_pdf_zzp:
	$(foreach ext, $(err_extensions), $(foreach file, log_$(target_pdf_zzp:.pdf=$(ext)), test -f $(file) && rm -v $(file) || echo No $(file));)

clean_rest:
	@$(foreach file, $(rest_files), test -f $(file) && rm -v $(file) || echo No $(file);)
