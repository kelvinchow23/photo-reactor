# LED-board thermal guidance

Applies to SDL4-0002 with XINGLIGHT XL-HD6070UGC-A2-BD, paired with the controller's 0.43 ohm current-sense resistors.

## Construction

- Native PCB: 55x55mm, two layers, nominal 1.0mm finished thickness. Confirm the actual order thickness before designing a clamp.
- LED on front; connectors and small components on rear.
- Central rear exposed thermal contact: 22x22mm. Preserve the surrounding 26x26mm component/track clearance.
- Thermal copper and via network are separate from all cable nets. The LED's internal slug connection is unspecified, so treat that copper as potentially live.
- Use an electrically insulating thermal interface between the PCB and heatsink. Anodizing is not a substitute for rated insulation.
- The selected shopping-list sink is Same Sky HSB08-212106, 21x21x6mm. The historical design envelope allowed a 25x25mm sink.
- The selected TIM is Bergquist GP1500R-0.010-02-0816, 0.254mm sheet. Its tack does not replace mechanical retention.
- Support the PCB and apply uniform contact pressure with a holder/clamp, without bending it or loading the LED lens. Keep sink fins exposed to air.

## Limits and remaining checks

The AL8860 nominal full-scale current is about 0.1/0.43 = 233mA. The LED's listed 2.8-3.4V forward range was measured at 350mA; electrical power and junction temperature must be established at the actual operating current.

The LED datasheet does not provide a usable junction-to-slug thermal resistance. Its 120C maximum junction rating cannot be translated directly into an approved PCB or heatsink temperature. Do not reuse the obsolete Lumileds thermal resistance or junction-temperature limits.

The brief LED bench checks do not establish sustained thermal performance. Validate LED current, interface contact, temperature rise and airflow in the assembled housing before continuous operation. Use an electrically isolated temperature measurement method; never short thermal copper to a grounded probe.

Check supplier acceptance of the LED's one-reflow, 220C/6s limits before repeating assembly. The completed prototype does not establish that a generic two-sided process complies.

## References

- [Exact LED drawing and specifications](references/XINGLIGHT_XL-HD6070UGC-A2-BD.pdf)
- [Mechanical STEP package](../outputs/mechanical/Rev-A/SDL4_REV_A_mechanical-models.zip)
- [Observed bench results](../../docs/bench-results.md)

Old Lumileds calculations and historical via-placement notes were retained locally as development history, not current acceptance criteria.
